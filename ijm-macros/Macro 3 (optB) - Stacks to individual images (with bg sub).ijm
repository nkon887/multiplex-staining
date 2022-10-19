// all the cropped stacks should be in one folder, no subfolders!
// Macro written by Adrien Guillot

dirS = getDirectory("Choose folder containing the cropped stacks");
dirD = getDirectory("Choose destination folder for single pictures");

pattern = ".*"; // for selecting all the files in the folder

filenames = getFileList(dirS);
count = 0;
for (i = 0; i < filenames.length; i++) {
	currFile = dirS+filenames[i];
	if(endsWith(currFile, ".tif") && matches(filenames[i], pattern)) { // process tif files matching regex
		open(currFile);
		count++;	
run("Stack to Images");
while (nImages>0) {
	title = getTitle();
	print("title: " + title);
	run("Subtract Background...", "rolling=50");
	saveAs("Tiff", dirD+getTitle());
	close();
}
}
}