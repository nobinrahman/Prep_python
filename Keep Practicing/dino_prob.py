# Two CSV files are provided. The first file contains statistics about various mammals. The second file contains additional data.
# Write a program to read in the data from files, Print the names of only the bipedal mammals from fastest to slowest. 
# Do not print any other information.
# speed = ((STRIDE_LENGTH / LEG_LENGTH) - 1) * SQRT(LEG_LENGTH * g)
# Where g = 9.8 m/s^2 (gravitational constant)

# $ cat dataset1.csv
# NAME,LEG_LENGTH,DIET
# Struthiomus,0.72,omnivore
# raptor,1.8,carnivore
# Triceratops,0.47,herbivore
# Euoplocephalus,2.6,herbivore
# Stegosaurus,1.50,herbivore
# Tyranno Rex,6.5,carnivore

# $ cat dataset2.csv
# NAME,STRIDE_LENGTH,STANCE
# Euoplocephalus,1.97,quadrupedal
# Stegosaurus,1.70,quadrupedal
# Tyranno Rex,4.76,bipedal
# Deinonychus,1.11,bipedal
# Struthiomus,1.24,bipedal
# raptorr,2.62,bipedal



import csv
import math

g = 9.8
file_path1 = "/Users/krahman/Documents/Cisco/Documents/Personal/Interview Prep/Automation/Meta Question/dataset1.csv"
file_path2 = "/Users/krahman/Documents/Cisco/Documents/Personal/Interview Prep/Automation/Meta Question/dataset2.csv"

# Step 1: Read dataset2, keep only bipedal dinos in a dict with stride_length
bipedal_data = {}
with open(file_path2, mode='r', encoding='utf-8-sig') as file2:
    reader2 = csv.DictReader(file2)
    for row in reader2:
        if row['STANCE'].lower() == 'bipedal':
            # Store stride length for bipedal dinos
            bipedal_data[row['NAME']] = float(row['STRIDE_LENGTH'])
print(bipedal_data)

# Step 2: Read dataset1, calculate speed only if NAME in bipedal_data
results = []
with open(file_path1, mode='r', encoding='utf-8-sig') as file1:
    reader1 = csv.DictReader(file1)
    for row in reader1:
        name = row['NAME']
        if name in bipedal_data:
            leg_length = float(row['LEG_LENGTH'])
            stride_length = bipedal_data[name]
            speed = ((stride_length / leg_length) - 1) * math.sqrt(leg_length * g)
            results.append((name, speed))

# Step 3: Sort from fastest to slowest and print names and speeds
results.sort(key=lambda x: x[1], reverse=True)
for name, speed in results:
    print(f"{name},{speed:.5f}")
















import csv
import math

file_path1 = "/Users/krahman/Documents/Cisco/Documents/Personal/Interview Prep/Automation/Meta Question/dataset1.csv"
file_path2 = "/Users/krahman/Documents/Cisco/Documents/Personal/Interview Prep/Automation/Meta Question/dataset2.csv"
g = 9.8
dataset1 = {}
dataset2 = {}
with open(file_path1, mode='r', encoding='utf-8-sig') as file1:
    content1 = csv.DictReader(file1)
    for row in content1:
        dino_name = row['NAME']
        dino_leg_length = float(row['LEG_LENGTH'])
        dino_diet = row['DIET']
        # print(f"{dino_name=}")
        # print(f"{dino_leg_length=}")
        # print(f"{dino_diet=}")
        dataset1[dino_name]={'dino_leg_length':dino_leg_length, 'dino_diet':dino_diet}
# print(dataset1)
with open(file_path2, mode='r', encoding='utf-8-sig') as file2:
    content2 = csv.DictReader(file2)
    for row in content2:
        dino_name = row['NAME']
        dino_stride_length = float(row['STRIDE_LENGTH'])
        dino_stance = row['STANCE']
        # print(f"{dino_name=}")
        # print(f"{dino_stride_length=}")
        # print(f"{dino_stance=}")
        dataset2[dino_name] = {"dino_stride_length":dino_stride_length,"dino_stance":dino_stance}
# print(dataset2)

bipedal_speed = []
for dino_name,stats in dataset2.items():
    # print(dataset2[dino_name]["dino_stance"])
    if dataset2[dino_name]["dino_stance"] == 'bipedal' and dino_name in dataset1:
        dino_leg_length = dataset1[dino_name]["dino_leg_length"]
        dino_stride_length = dataset2[dino_name]["dino_stride_length"]
        # Formuls: speed = ((STRIDE_LENGTH / LEG_LENGTH) - 1) * SQRT(LEG_LENGTH * g)
        speed = ((dino_stride_length / dino_leg_length) - 1) * math.sqrt(dino_leg_length * 9.8)
        # print((dino_name, speed))
        bipedal_speed.append((dino_name, speed))
print(bipedal_speed)

bipedal_speed.sort(key=lambda x:x[1], reverse=True)

print(bipedal_speed)

for dino in bipedal_speed:
    print(dino[0])



