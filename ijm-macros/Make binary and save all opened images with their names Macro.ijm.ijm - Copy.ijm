// Macro written by Adrien Guillot

while (nImages>0) {
	title = getTitle();
	print("title: " + title);
	run("16-bit");
setOption("ScaleConversions", true);
run("8-bit");
setOption("BlackBackground", true);
run("Make Binary");
	saveAs("Tiff", "J:/Adrien/"+title);
	close();
}
