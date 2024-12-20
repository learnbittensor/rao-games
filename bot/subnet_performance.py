import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import bittensor as bt

class SubnetPerformance:
    def __init__(self, window_size: int = 100):
        self.emission_rates = []
        self.prices = []
        self.window_size = window_size
        self.alpha_out = self.tao_in = self.emission = self.price = None
        self.model = RandomForestRegressor(n_estimators=100)
        self.model_fitted = False

    def update(self, subnet_info):
        if isinstance(subnet_info, dict):
            self.emission_rates = subnet_info.get('emission_rates', [])
            self.prices = subnet_info.get('prices', [])
        else:
            self.alpha_out, self.tao_in, self.emission, self.price = map(float, (subnet_info.alpha_out, subnet_info.tao_in, subnet_info.emission, subnet_info.price))
            self.emission_rates.append(self.emission)
            self.prices.append(self.price)
            if len(self.emission_rates) > self.window_size:
                self.emission_rates.pop(0)
                self.prices.pop(0)
        self.train_model()
        return self

    def train_model(self):
        if len(self.prices) > 20:
            X = np.array([self.emission_rates[:-1], self.prices[:-1]]).T
            y = np.array(self.prices[1:])
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            self.model.fit(X_train, y_train)
            y_pred = self.model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            bt.logging.info(f"Model MSE: {mse}")
            self.model_fitted = True

    def predict_next_price(self):
        if not self.model_fitted:
            return 0
        if len(self.prices) > 0:
            X = np.array([[self.emission_rates[-1], self.prices[-1]]])
            return self.model.predict(X)[0]
        return 0

    @property
    def current_emission_rate(self) -> float:
        return self.emission_rates[-1] if self.emission_rates else 0

    @property
    def current_price(self) -> float:
        return self.prices[-1] if self.prices else 0

    @property
    def trend(self) -> float:
        return self.current_price - self.current_emission_rate

    @property
    def volatility(self) -> float:
        return np.std(self.prices) if len(self.prices) > 1 else 0

    @property
    def inflation_rate(self) -> float:
        return (self.alpha_out + 1000) / self.alpha_out - 1.0 if self.alpha_out > 0 else 0

    @property
    def price_drop_percentage(self) -> float:
        if len(self.prices) > 1:
            return (self.prices[0] - self.prices[-1]) / self.prices[0]
        return 0
