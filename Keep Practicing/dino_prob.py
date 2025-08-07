#Dinosaur problem Meta
# Formuls: speed = ((STRIDE_LENGTH / LEG_LENGTH) - 1) * SQRT(LEG_LENGTH * g)
# You are given two data files in CSV format. One file contains statistics 
# about various dinosaurs. The other contains additional data. Given the 
# following formula, speed = ((STRIDE_LENGTH / LEG_LENGTH) - 1) * SQRT(LEG_LENGTH * g), 
# where g = 9.8 m/s^2 (gravitational constant), write a program to read 
# in the data files from disk. It must then print the names of only the 
# bipedal dinosaurs, from fastest to slowest.
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