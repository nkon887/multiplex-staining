//

#@ File(label = "Input directory", style = "directory") input // select the main folder that comprises ALL the subfolders
#@ File(label = "Output directory", style = "directory") output //Output directory
#@ String(label = "File suffix", value = ".tif") suffix
#@ String(label = "1stChannel", value = "0dapi") firstChannel
#@ Boolean forceSave

subfolders=getSubfolders(input);
for (i = 0; i < lengthOf(subfolders); i++) {
    subfolderFiles = getFilesFromSubfolder(subfolders[i]);
    //print(subfolderFiles[2]);

    dapiFiles = getChannelFiles(subfolderFiles, ".*"+ firstChannel +".*");
    //Array.print(dapiFiles);
    dapiFiles =    Array.deleteValue(dapiFiles, "" );
    channels=getChannels(subfolderFiles,firstChannel);
    if (channels.length==0) {
    	exit("Channels could not be identified. Please check the filename");
    }
    selectedDapiAndChannels=generateDialogAndgetValues(dapiFiles, channels);

    dapiFileForMerge=selectedDapiAndChannels[0];
    channels=Array.slice(selectedDapiAndChannels, 1, selectedDapiAndChannels.length);
    channelFiles=newArray();
    for (j = 0; j < channels.length; j++) {
        channel=channels[j];
         //Array.print(subfolderFiles);
         str=" "+channel + " ";
         cnl=split(str, " ");
        channelFilesToAdd=getChannelFiles(subfolderFiles, ".*"+ cnl[0] +"\\.tif");
        channelFiles=Array.concat(channelFiles,channelFilesToAdd);
        //Array.print(channelFilesToAdd);
    }
    channelFiles=Array.deleteValue(channelFiles, "");
    //Array.print(channels);
    //Array.print(channelFiles);
    process(dapiFileForMerge, channelFiles, output, suffix, forceSave);
    run("Close All");
}
function generateDialogAndgetValues (dapiFiles, channels) {
    Dialog.create("Channels");
    Dialog.addMessage("Choose dapi image  you want to use for merge");
    if (dapiFiles.length==0) {
    	exit("Image file of dapi channel isn't found. Please check the filename or change  it in the \"Parameter settings\" ");
    }
    Dialog.addChoice("Dapi:", dapiFiles);
    Dialog.addMessage("Choose images of channels you want to combine with dapi image");

    labels = channels;
    n=channels.length;
    defaults = newArray(n);
    rows =n/4;
    columns=4;
    if (!((n%2)==0)){
    	Dialog.addCheckbox(channels[channels.length-1], false);
    	n=n-1;
    }
    for (i=0; i<n; i++) {
        labels[i] = labels[i]+" ";
        defaults[i] = false;
   }
   Dialog.addCheckboxGroup(rows,columns,labels,defaults);
    // Show the GUI with all parameters to add
    Dialog.show();
     // Once the Dialog is OKed the rest of the code is executed
    // ie one can recover the values in order of appearance
    inChoiceDapi  = Dialog.getChoice();
    //inBooleanBackground = Dialog.getCheckbox();
    // print("Choice:", inChoiceDapi);
    //print("with/withoutbg (1=True, 0=False):", inBooleanBackground);
    selectedChannels=newArray();
    if(Dialog.getCheckbox()) {
    	value=newArray(channels[channels.length-1]);
        selectedChannels=Array.concat(selectedChannels, value );
    }
    for (i=0; i<n; i++) {
//    	print(labels[i]+": "+Dialog.getCheckbox());
        if(Dialog.getCheckbox()) {
            value=newArray(labels[i]);
            selectedChannels=Array.concat(selectedChannels, value );
        }
    }

    //Array.print(selectedChannels);
    return Array.concat(inChoiceDapi,selectedChannels);


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
    result = newArray("");
    //print(pattern);
    if (matches(filePath, pattern)) {
        result= newArray(filePath);
    }
    //print(result);
    return result;
}

function getChannelFiles(subfolderFiles, regex) {
    channelFiles = newArray();
    for (i = 0; i < lengthOf(subfolderFiles); i++) {
        match=getMatch(subfolderFiles[i], regex);
        channelFiles=Array.concat(channelFiles, match);
    //    Array.print(channelFiles);
    }
    //Array.print(channelFiles);
    return channelFiles;
}
function ArrayUnique(array) {
    array     = Array.sort(array);
    array     = Array.concat(array, 999999);
    uniqueA = newArray();
    i = 0;
       while (i<(array.length)-1) {
        if (array[i] == array[(i)+1]) {
            //print("found: "+array[i]);
        } else {
            uniqueA = Array.concat(uniqueA, array[i]);
        }
           i++;
       }
    return uniqueA;
}

function getChannels(subfolderFiles, Channel) {
    channels = newArray();
    for (i = 0; i < lengthOf(subfolderFiles); i++) {
        filename=File.getName(subfolderFiles[i]);
        if(endsWith(filename, ".tif") && !matches(filename, ".*"+ Channel +".*")){
            filename=File.getNameWithoutExtension(filename);
            substrings=split(filename,"_");
            string=String.join(Array.slice(substrings, 2, substrings.length), "_");
            //print(string);
            channel=newArray(string);
            channels=Array.concat(channels,channel);
            uniqueChannels = ArrayUnique(channels);
        }
    }
    //Array.print(uniqueChannels);
    return uniqueChannels;
}

function process(dapiFile, channelFiles, output, suffix, forceSave) {
    for(i=0;i<channelFiles.length;i++) {
      name = File.getNameWithoutExtension(channelFiles[i])+"_merged_dapi";
      open(dapiFile);
      open(channelFiles[i]);
      run("Merge Channels...", "c3=["+File.getName(dapiFile)+ "] c1=["+File.getName(channelFiles[i])+ "] keep");
      subfolderArray=split(File.getNameWithoutExtension(channelFiles[i]), "_");
      sampleFolder = output + File.separator + subfolderArray[0];
      print(forceSave);
      if (!File.exists(sampleFolder)) {
      File.makeDirectory(sampleFolder);
      }
      savePath=sampleFolder+File.separator+name;
      if(File.exists(savePath+".tif")==0) {
      	saveAs(suffix, savePath);
      }
      else {
    	if (forceSave==1) {
    		File.delete(savePath+".tif");
    		saveAs(suffix, savePath);
    		}
    	}
      }
}