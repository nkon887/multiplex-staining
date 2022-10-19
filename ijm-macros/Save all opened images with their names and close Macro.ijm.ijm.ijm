while (nImages>0) {
	title = getTitle();
	print("title: " + title);
	saveAs("Tiff", "J:/Adrien/"+title);
	close();
}
