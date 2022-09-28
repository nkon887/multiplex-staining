import os


# Function to rename multiple files
def main():
    i = 0
    path = input("Enter the path of your directory: ")
    for subfolder in os.listdir(path):
        for filename in subfolder:
            my_source = path + filename
            filename.replace("-Stitching", "")
            filename.replace("-Image Export-01_h0s0", "")
            filename.replace("x0-24175y0-13702_ORG", "")
            "c1_ORG"  -->"0dapi"
            "c3_ORG", ""
            "c4_ORG"-->""
            "11_"
            my_dest = filename + ".tif"
            my_dest = path + my_dest
            # rename() function will
            # rename all the files
            os.rename(my_source, my_dest)
            i += 1


# Driver Code
if __name__ == '__main__':
    # Calling main() function
    main()


filesRename = ['demo_1.txt', 'demo_2.txt', 'demo_3.txt', ]
folder = r"E:\docs\\"

# Iterate
for file in os.listdir(folder):
    # Checking if the file is present in the list
    if file in filesRename:
        oldName = os.path.join(folder, file)
        n = os.path.splitext(file)[0]

        b = n + '_new' + '.txt'
        newName = os.path.join(folder, b)

        # Rename the file
        os.rename(oldName, newName)

res = os.listdir(folder)
print(res)
