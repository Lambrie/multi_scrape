import csv, os, math

file_names = ["industry1.csv","industry2.csv","industry3.csv","industry4.csv"]
number_splits = 4

for file_number, input_file in enumerate(file_names):
    rows = []
    print(f"Start -> {input_file}")
    with open(os.path.join("data","input",f"{input_file}"), mode='r', newline='\n', encoding='utf-8') as infile:
        csv_reader = csv.DictReader(infile, delimiter=',', quotechar='"')
        for row in csv_reader:
            rows.append(row)
    split_rows = int(math.ceil(len(rows) / number_splits))
    headers = rows[0].keys()
    for i in range(number_splits):
        with open(os.path.join("data", "input", f"industry{file_number+1}_{i+1}.csv"), mode='w+', newline='\n', encoding='utf-8') as infile:
            writer = csv.DictWriter(infile, headers)
            writer.writeheader()
            writer.writerows(rows[split_rows*i:(i+1)*split_rows])
    print(f"Finished -> {input_file}")