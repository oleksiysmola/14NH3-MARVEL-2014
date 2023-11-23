import pandas as pd
from pandarallel import pandarallel
pandarallel.initialize(progress_bar=True)

pd.set_option('display.float_format', '{:.6f}'.format)

marvelColumns = ["nu1", "nu2", "nu3", "nu4", "L3", "L4", "J", "K", "inv", "Gamma", "Nb", "Em", "Uncertainty", "Transitions"]

marvelEnergies = pd.read_csv("14NH3-NewEnergies.txt", delim_whitespace=True, names=marvelColumns, dtype=str)

symmetryMap = {
    "A1'": "1",
    "A2'": "2",
    "E'": "3",
    "A1\"": "4",
    "A2\"": "5",
    "E\"": "6"
}

marvelEnergies["Gamma"] = marvelEnergies["Gamma"].map(symmetryMap)

statesFileColumns = ["i", "E", "g", "J", "weight", "p", "Gamma", "Nb", "n1", "n2", "n3", "n4", "l3", "l4", "inversion", "J'", "K'", "pRot", "v1", "v2", "v3", "v4", "v5", "v6", "GammaVib", "Calc"]
states = pd.read_csv("../14N-1H3__CoYuTe.states", delim_whitespace=True, names=statesFileColumns, dtype=str)

def generateTagColumn(dataFrame):
    dataFrame["Tag"] = dataFrame["J"] + "-" + dataFrame["Gamma"] + "-" + dataFrame["Nb"]
    return dataFrame

marvelEnergies = generateTagColumn(marvelEnergies)
states = generateTagColumn(states)

columnsToConvertToInteger = ["J","n1", "n2", "n3", "n4"]
for column in columnsToConvertToInteger:
    states[column] = states[column].astype(int)

states = pd.merge(states, marvelEnergies[["Tag", "Em", "Uncertainty"]], on="Tag", how="left")

columnsToConvertToFloat = ["Em", "E", "Calc", "weight", "Uncertainty"]
for column in columnsToConvertToFloat:
    states[column] = states[column].astype(float)
    
pd.set_option('display.float_format', '{:.6f}'.format)

def marvelise(row):
    # Parameters that get used for the calculated uncertainty
    deltaB = 0.002
    deltaOmega = 0.3
    calculatedEnergy = row["Calc"]
    if row["Em"] >= 0:
        row["Marvel"] = "Ma"
        marvelUncertainty = row["Uncertainty"] 
        row["weight"] = f"{marvelUncertainty:.{6}f}"
        marvelEnergy = row["Em"] 
        row["E"] = f"{marvelEnergy:.{6}f}" 
    else:
        row["Marvel"] = "Ca"
        estimatedUncertainty = deltaB*row["J"]*(row["J"] + 1) + deltaOmega*(row["n1"] + row["n2"] + row["n3"] + row["n4"])
        row["weight"] = f"{estimatedUncertainty:.{6}f}"
        row["E"] = f"{calculatedEnergy:.{6}f}"
    row["Calc"] = f"{calculatedEnergy:.{6}f}"
    return row

print("\n")
print("Beginning Marvelisation...")
states = states.parallel_apply(lambda x:marvelise(x), result_type="expand", axis=1)
print("\n")
print("Marvelisation complete!")
statesFileColumns = ["i", "E", "g", "J", "weight", "p", "Gamma", "Nb", "n1", "n2", "n3", "n4", "l3", "l4", "inversion", "J'", "K'", "pRot", "v1", "v2", "v3", "v4", "v5", "v6", "GammaVib", "Marvel", "Calc"]
states = states[statesFileColumns]

columnWidth = 1
def formatColumns(value):
    global columnWidth
    return f'{value: >{columnWidth}}'
    
def reformatColumns(dataFrame, columnReformattingOptions):
    global columnWidth 
    collectedReformattedColumns = []
    for key in columnReformattingOptions.keys():
        columnWidth = key
        dataFrameToReformat = dataFrame[columnReformattingOptions[key]]
        collectedReformattedColumns += [dataFrameToReformat.applymap(formatColumns)]
    dataFrame = pd.concat(collectedReformattedColumns, axis=1, join="inner")
    return dataFrame

columnReformattingOptions = {
    12: ['i', 'E', 'weight', 'Calc'],
    6: ["g", "n1", "J'", "v1"],
    2: ["Gamma", "pRot"],
    10: ["Nb"],
    3: ["n2", "n3", "n4", "l4", "K'", "v2", "v3", "v4", "v5", "v6", "Marvel"],
    7: ["J", "l3"],
    5: ["inversion", "GammaVib"],
    1: ["p"]
}
print("\n")
print("Reformatting columns...")
states = reformatColumns(states, columnReformattingOptions)
# def formatEnergy(value):
#     return f'{value: >12}'

# columnsToFormat = ['i', 'E', 'weight', 'Calc']
# statesColumnsToFormat = states[columnsToFormat]
# statesColumnsToFormat = statesColumnsToFormat.applymap(formatEnergy)
# listOfFormattedColumns = [statesColumnsToFormat]

    
print("\n")
print("Reformatting complete!")
# unformattedColumns = []
# for column in statesFileColumns:
#     if column not in columnsToFormat:
#         unformattedColumns += [column]
# states = states[unformattedColumns]
    

pd.set_option('display.float_format', '{:.6f}'.format)

# states = pd.concat([states] + listOfFormattedColumns, axis=1, join="inner")
states = states[statesFileColumns]
print("\n")
print("Concationation complete!")
print(states.head(20).to_string(index=False))
print("\n")
print("Printing states file...")
states = states.to_string(index=False, header=False)
statesFile = "14N-1H3__CoYuTe-Marvelised-2024.states"
with open(statesFile, "w+") as FileToWriteTo:
    FileToWriteTo.write(states)
print("New states file ready!")