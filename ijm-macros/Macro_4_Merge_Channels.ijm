//

#@File(label = "Input directory", style = "directory") input // select the main folder that comprises ALL the subfolders
#@File(label = "Output directory", style = "directory") output
#@String(label = "File suffix", value = ".tif") suffix
#@String(label = "1stChannel", value = "DAPI") firstChannel
#@String (choices={"CD8", "CD20", "IBA1", "MPO"}, style="radioButtonHorizontal") secondChannelToChoose
subfolders=getSubfolders(input);
for (i = 0; i < lengthOf(subfolders); i++) {
	subfolderFiles = getFilesFromSubfolder(subfolders[i]);
	print(subfolderFiles[0]);
	//dapiFiles = getChannelFiles(subfolderFiles, firstChannel);
	//print(dapiFiles[0]);
	//#@String (choices=dapiFiles, style="radioButtonHorizontal") DapiChannelsToChoose
	}
//print(subfolders[0]);

//var inputDir
//var outputDir
//inputDir = File.getName(input);


function getSubfolders(inputDir) {
	subfolderList = getFileList(inputDir);
	for (i = 0; i < lengthOf(subfolderList); i++) {
    subfolderList[i]= input + File.separator + subfolderList[i];
    subfolderList[i]=subfolderList[i].replace("/", "");
	}
	return subfolderList;
}
function getFilesFromSubfolder(subfolder){
    fileList = getFileList(subfolder);
    for (i = 0; i < lengthOf(fileList); i++) {
 		fileList[i]= subfolder + File.separator + fileList[i];
    }
    return fileList;
}

function getMatch (filePath, pattern) {
	if (matches(filePath, pattern)) {
		print(filePath);
		return filePath;
	}
}

function getChannelFiles(subfolderFiles, Channel) {
	channelFiles = newArray();
	
	//for  (i = 0; i < lengthOf(subfolderFiles); i++) {
	//	channelFiles=Array.concat(channelFiles, getMatch(subfolderFiles[i], ".*"+ Channel +".*") );		
	//}
	//print(channelFiles[0]);
	return channelFiles;
}

/*function process(subfolder, subfolderFiles,Channel) {
	for (i = 0; i < lengthOf(subfolderFiles); i++) {
		getMatch(subfolderFiles[i],  "" + " " + subfolder+"-_h0s0_"+ Channel+"_"+".*".tif")
			substring(string, index);
	}

    run("Merge Channels...", "c2=[220630 4421-14-2F_s0_0dapi_bgsub.tif] c6=[220630 4421-14-2F_s0_CD8_bgsub-1.tif] keep");
    
    close();
}*/
