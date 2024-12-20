import bittensor as bt
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

number_of_subnets = 32
number_of_blocks = 10000
subnets = bt.subtensor().get_all_subnet_dynamic_info()
num_subnets = len(subnets[1:number_of_subnets])

heatmap_data = np.zeros((num_subnets, num_subnets))

for i, subnet_a in enumerate(subnets[1:number_of_subnets]):
    for j, subnet_b in enumerate(subnets[1:number_of_subnets]):
        next_price_a = (subnet_a.tao_in.tao + subnet_a.emission.tao * number_of_blocks) / (subnet_a.alpha_in.tao + 1 * number_of_blocks)
        price_drop_a =  -1 * (next_price_a - subnet_a.price.tao) / subnet_a.price.tao
        inflation_a = ((subnet_a.alpha_out.tao + number_of_blocks) / (subnet_a.alpha_out.tao)) - 1.0
        return_a = inflation_a - price_drop_a

        next_price_b = (subnet_b.tao_in.tao + subnet_b.emission.tao * number_of_blocks) / (subnet_b.alpha_in.tao + 1 * number_of_blocks)
        price_drop_b =  -1 * (next_price_b - subnet_b.price.tao) / subnet_b.price.tao
        inflation_b = ((subnet_b.alpha_out.tao + number_of_blocks) / (subnet_b.alpha_out.tao)) - 1.0
        return_b = inflation_b - price_drop_b

        swap_return_a_to_b = return_b - return_a
        heatmap_data[i, j] = swap_return_a_to_b

plt.figure(figsize=(12, 10))
sns.heatmap(heatmap_data, cmap='coolwarm', center=0)
plt.title('Increase in return by swapping from subnet A to subnet B')
plt.xlabel('Subnet B')
plt.ylabel('Subnet A')

plt.savefig('subnet_swap_heatmap.png', dpi=300, bbox_inches='tight')

plt.close()
