// make sure all the pictures are per section per day in a single subfolder containing 4 pictures
// one of the pictures should be called "0dapi" and will be placed on top tof the stacks, then used for the alignment
// Macro written by Adrien Guillot

#@File(label = "Input directory", style = "directory") input // select the main folder that comprises ALL the subfolders
#@File(label = "Output directory", style = "directory") output
#@String(label = "File suffix", value = ".tif") suffix


    var outputDir
    var inputDir 
    outputDir = File.getName(output);
    inputDir = File.getName(input);	
    
	processFolder(input);
    	
    // function to scan folders/subfolders/files to find files with correct suffix
    function processFolder(input) {
    	list = getFileList(input);
    	for (i = 0; i < list.length; i++) {
    		if(File.isDirectory(input + File.separator + list[i])) {
    			tempInputDir = input + File.separator + list[i];
    			saveDir = replace(tempInputDir, inputDir, outputDir); // replaces the input folder name (string) with the output folder name (string)
    			File.makeDirectory(saveDir);
    			processFolder("" + input + File.separator + list[i]);
    		}
             if(endsWith(list[i], suffix)) {
				processFile(input, output, list[i]);
				i = list.length;
    		}
    	}
    }
    
    function processFile(input, output, file) {
run("Image Sequence...", "open=input sort");
run("Subtract Background...", "rolling=50");
run("Stack to Hyperstack...", "order=xyczt(default) channels=3 slices=1 frames=1 display=Grayscale");
title = File.getName(input);
		print("title: " + title);
			saveAs("Tiff", output+File.separator+title); // pay attention to this path and make sure it is correct
print("Saving to: " + outputDir);
close();
}