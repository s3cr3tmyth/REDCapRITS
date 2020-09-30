import numpy as np
import pandas as pd
import re


pd.set_option('display.max_columns', 28)
pd.set_option('display.max_rows', 10)

data = pd.read_csv("../R/tests/testthat/data/ExampleProject_DATA_2018-06-07_1129.csv")
meta = pd.read_csv("../R/tests/testthat/data/ExampleProject_DataDictionary_2018-06-07.csv")

# print(data.head(10))
# print("\n",meta.head(10))

# data.columns = data.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')

v_names = list(data.columns)
m_names = list(meta.columns)

# print(v_names)

forms = ["repeating", "all"]
primary_table_name = "sale"

# Check to see if there were any repeating instruments
if (forms == "repeating" and "redcap_repeat_instrument" not in v_names):
    print("There are no repeating instruments in this dataset.")
else:
    print("You are good to go")

data.redcap_repeat_instrument = data.redcap_repeat_instrument.fillna("")

# print(meta.info())


# cat_columns = data.select_dtypes(['category']).columns
# df[cat_columns] = df[cat_columns].apply(lambda x: x.cat.codes)


# v_names and meta function

def match_fields_to_form(meta, v_names):

    fields = meta.loc[(meta['Field Type'] != "descriptive") & (meta['Field Type'] != "checkbox")
    , ['Field Name','Form Name']]

    # print(fields)

    unique_form_names = meta["Form Name"].unique()

    temp = [str(i)+ '_complete' for i in unique_form_names]

    # columns = ['field_name','form_name']

    form_complete_fields = pd.DataFrame(
        {'Field Name': temp,
        'Form Name': unique_form_names
        })

    # print(form_complete_fields)

    fields = fields.append(form_complete_fields, ignore_index=True)

    # print(fields)

    temp2 = [str(i)+ '_timestamp' for i in unique_form_names]

    # print(temp2)

    timestamps = [x for x in v_names if x in temp2]


    if len(timestamps):
        timestamp_fields = pd.DataFrame(
        {'Field Name': timestamps,
        'Form Name': re.sub("_timestamp$", "", timestamps)
        })
        fields = fields.append(timestamp_fields, ignore_index=True)



    if (any(meta['Field Type'] == "checkbox")):
        checkbox_basenames = meta.loc[(meta['Field Type'] == "checkbox"), ['Field Name','Form Name']]
        temp3 = [str for str in v_names if
                any(sub in str for sub in checkbox_basenames['Field Name'].to_list())] 
        checkbox_fields = pd.DataFrame(
        {'Field Name': temp3
        })
        checkbox_fields['F_dummy'] = checkbox_fields['Field Name'].str.split('___',expand=True)[0]
        zz = checkbox_fields.merge(checkbox_basenames, left_on=['F_dummy'],right_on=['Field Name'], how='left')
        zz = zz.drop(['F_dummy','Field Name_y'],axis = 1)
        zz = zz.rename(columns={"Field Name_x": "Field Name"})
        
        fields = fields.append(zz, ignore_index=True)

    return fields

### End of function I 

fields = match_fields_to_form(meta, v_names)


r = re.compile("^redcap_(?!(repeat)).*")
newlist = list(filter(r.match, v_names))
universal_fields = [v_names[0]] + newlist


if "redcap_repeat_instrument" in v_names: 
    r = re.compile("^redcap_repeat.*")
    repeat_instrument_fields = list(filter(r.match, v_names))


subtables = data["redcap_repeat_instrument"].unique()
subtables = list(filter(None, subtables))


# out = dict(iter(data.groupby('redcap_repeat_instrument')))

# out = list(data.groupby('redcap_repeat_instrument'))
# out = data.groupby('redcap_repeat_instrument')  
# out = [out.get_group(x) for x in out.groups]

cname = []


for out, n in data.groupby('redcap_repeat_instrument'):
    cname.append(out)
    primary_table_index = out.index("")

if (forms == "repeating" and primary_table_name in subtables):
    print("The label given to the primary table is already used by a repeating instrument. The primary table label will be left blank.")
    primary_table_name = ""
elif (primary_table_name > ""): 
    primary_table_name = cname[primary_table_index]


for i in cname:
    if i == primary_table_name:
        # for out, n in data.groupby('redcap_repeat_instrument').filter(lambda x: x == i):
        n = data[data['redcap_repeat_instrument'] == i]
        x = fields[~fields.iloc[:,1].isin(subtables)]
        x = universal_fields + list(x.iloc[:,0])
        out_fields = list(set([v_names.index(i) for i in x]))
        table1 = n.iloc[: , out_fields]

    # else: 
    #     n = data[data['redcap_repeat_instrument'] == i]
    #     x = fields[fields.iloc[:,1] == i]
    #     x = universal_fields + repeat_instrument_fields + list(x.iloc[:,0])
    #     out_fields = list(set([v_names.index(i) for i in x]))
    #     table1 = n.iloc[: , out_fields]


# function II

def split_non_repeating_forms(table, universal_fields, fields):
    xxx = list(table.columns)
    off = []    
    forms = fields.iloc[:, 1].unique()

    for i in range(len(forms)):
        d1 = list(fields.iloc[:,0][fields.iloc[:,1] == forms[i]])

        results_list = [d1, universal_fields]

        results_union = set().union(*results_list)

        of = list(set([xxx.index(i) for i in results_union]))
        off.append(of)
    tables = []
    for i in range(len(off)):
        table1 = table.iloc[: , off[i]]
        tables.append(table1)

    return tables


# funct II end
 
# if (forms == all):

tables = split_non_repeating_forms(table1, universal_fields, fields[~fields.iloc[:,1].isin(subtables)])

# else:

#     tables = split_non_repeating_forms(data, universal_fields, fields)

print(tables)
