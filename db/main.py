import chardet

# Detect encoding of the file
with open('Kazakhstan_Water_Pollution_Dataset.xlsx', 'rb') as f:
    result = chardet.detect(f.read())

print(result)
