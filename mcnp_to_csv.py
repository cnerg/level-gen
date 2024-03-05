# 1. generate array of boundaries for x, y, and z
# 2. generate array of centroid (x,y,z), result, relative error
import argparse
import os

def mcnp_to_csv(mcnpFile, outputFile):
    # append output filename with .csv regardless of what its file extension is
    output_filename, _ = os.path.splitext(outputFile)
    output_filename += ".csv"

    # open files
    with open(mcnpFile, 'r') as mcnpFile, open(output_filename, 'w') as outputFile:
        # get array of boundaries for x,y,z
        # 1a. find line that has x boundaries
        mcnpLine = mcnpFile.readline()
        while "X direction:" not in mcnpLine:
            mcnpLine = mcnpFile.readline()
        # 1b. split line into all the boundaries, write to file with comma separation
        # do this 3 times for the 3 axes
        num_dims = 3
        for dim in range(num_dims):
            outputStr = ','.join(mcnpLine.strip().split()[2:]) + '\n'
            outputFile.write(outputStr)
            mcnpLine = mcnpFile.readline()

        # advance to the centroid and results section
        while "Result" not in mcnpLine:
            mcnpLine = mcnpFile.readline()

        # 2. write all the centroid and result info to the csv file
        mcnpLine = mcnpFile.readline() # this will have the first centroid (x,y,z) and result
        # iterate through all voxels
        while mcnpLine:
            outputStr = ','.join(mcnpLine.strip().split()[1:]) + '\n'
            outputFile.write(outputStr)
            mcnpLine = mcnpFile.readline()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog = "MCNP mesh tally to .csv converter")
    parser.add_argument("mcnpFile", type = str, help = "input mcnp .txt filename")
    parser.add_argument("outputFile", type = str, help = "output .csv filename")

    args = parser.parse_args()

    mcnp_to_csv(args.mcnpFile, args.outputFile)


