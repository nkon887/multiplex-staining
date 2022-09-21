// all the concatenates should be in one folder, no subfolders!
// at the end, check alignment before deleting concatenates! and crop stacks as necessary before going to the next macro (leave them as stacks)
// Macro written by Adrien Guillot

dirS = getDirectory("Choose folder containing the concatenates");
dirD = getDirectory("Choose destination folder for aligned stacks");


pattern = ".*"; // for selecting all the files in the folder

filenames = getFileList(dirS);
count = 0;
for (i = 0; i < filenames.length; i++) {
	currFile = dirS+filenames[i];
	if(endsWith(currFile, ".tif") && matches(filenames[i], pattern)) { // process tif files matching regex
		open(currFile);
		count++;	

run("HyperStackReg ", "transformation=Affine channel1");
	title = getTitle();
	print("title: " + title);
	run("Hyperstack to Stack");
	saveAs("Tiff", dirD+getTitle());
	close();
	close();
	}
}