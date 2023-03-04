input = "S:/C13/Microscopy-core/zkobus/230220_Copies_DAPI_for_new_masks/output/binary/";
output = "S:/C13/Microscopy-core/zkobus/230220_Copies_DAPI_for_new_masks/output/binary_size_correct/";
inputOrigin= "S:/C13/Microscopy-core/zkobus/230220_Copies_DAPI_for_new_masks/";
list = getFileList(input);
setBatchMode(true);
for (i = 0; i < list.length; i++){
    output_file = output + list[i];
    if(!File.exists(output_file)){
        action(input, output, inputOrigin, list[i]);
    }
}        
setBatchMode(false);
function action(input, output, inputOrigin, filename) {
    open(input + filename);
    run("Create Selection");
    run("ROI Manager...");
    roiManager("Add");
    print(filename);
    file_split=substring(filename, 0, lengthOf(filename) - 15);
	print(file_split);
    origin_file = file_split+".tif";
    open(inputOrigin + origin_file);
    selectWindow(origin_file);
    roiManager("Select", 0);
	//selectWindow("02_9034_1r5-01-17_0dapi_bgsubgrowth0mask.tif");
    selectWindow(origin_file);
	//selectWindow("02_9034_1r5-01-17_0dapi_bgsubgrowth0mask.tif");
	//selectWindow("02_9034_1r5-01-17_0dapi.tif");
    run("Create Mask");
    saveAs("Tiff", output+filename);
    run("Close");
    while (nImages>0) { 
        selectImage(nImages); 
        close(); 
    }  

}