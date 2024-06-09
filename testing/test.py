import numpy as np
import time

# Define the start, stop, and step values
start = 1
stop = 2
step = 0.000001  # Step of 10^-3

# Create the list of floating-point numbers
numbers = [start + i * step for i in range(int((stop - start) / step) + 1)]


# Benchmark for loop with *
start_time = time.time()
total_sum_loop = 0
for num in numbers:
    total_sum_loop += num * num
end_time = time.time()
loop_time = end_time - start_time

# Benchmark np.sum
start_time = time.time()
total_sum_np = np.sum(np.array(numbers) * numbers)
end_time = time.time()
np_sum_time = end_time - start_time

print("Total sum using np.sum:", total_sum_np)
print("Time taken by np.sum:", np_sum_time)
print("Total sum using for loop:", total_sum_loop)
print("Time taken by for loop with +:", loop_time)
