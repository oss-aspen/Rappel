import csv
import pandas as pd
#files from command line output via source graph
files = ['bulk.txt', 'a_license.txt', 'c_license.txt', 'e_license.txt', 'i_license.txt',
         'l_license.txt', 'm_license.txt', 'n_license.txt',
         'p_license.txt', 's_license.txt', 'z_license.txt']

lines = []
for f in files:
    myfile = open(f)
    for line in myfile:
        lines.append(line)

link_pairs = []
for num in range(len(lines)):
    if lines[num].startswith('github'):
        license = lines[num+2][12:]
        link_pairs.append([lines[num].split(" ", 1)[0], license])

print(len(link_pairs))

fields = ['github_link', 'license']
print(link_pairs[:10])

df = pd.DataFrame(link_pairs, columns=fields)
df = df.drop_duplicates(subset=['github_link'])
print(df.shape)
df.to_csv('final.csv', index=False)
