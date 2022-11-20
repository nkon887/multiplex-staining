import sys
import os
from ij import IJ, ImagePlus, VirtualStack
from ij.plugin.filter import BackgroundSubtracter
from mpicbg.ij.plugin import NormalizeLocalContrast
from ij.gui import GenericDialog
from ij.io import FileSaver
from ij.gui import WaitForUserDialog

# sys.path.append(os.path.abspath(os.getcwd()))
sys.path.append(os.path.abspath("C:/Users/nko88/PycharmProjects/muliplex-staining/py_pipeline"))
import config


class ExtractedImagesFromStack(VirtualStack):
    def __init__(self, stack, params, tiff_contrast_adjusted_no_bg_sub_path,
                 tiff_no_contrast_adjusted_no_bg_sub_path, tiff_no_contrast_adjusted_bg_sub_path,
                 tiff_contrast_adjusted_bg_sub_path):
        # Constructor: tell the superclass VirtualStack about the dimensions
        super(VirtualStack, self).__init__(stack.getWidth(), stack.getHeight(), stack.size())
        self.stack = stack
        self.params = params
        self.tiff_contrast_adjusted_no_bg_sub_path = tiff_contrast_adjusted_no_bg_sub_path
        self.tiff_no_contrast_adjusted_no_bg_sub_path = tiff_no_contrast_adjusted_no_bg_sub_path
        self.tiff_no_contrast_adjusted_bg_sub_path = tiff_no_contrast_adjusted_bg_sub_path
        self.tiff_contrast_adjusted_bg_sub_path = tiff_contrast_adjusted_bg_sub_path

    def getProcessor(self, n):
        IJ.log("finished")
        # background settings
        radius = self.params["radius"]
        create_background = self.params["createBackground"]
        light_background = self.params["lightBackground"]
        use_paraboloid = self.params["useParaboloid"]
        do_presmooth = self.params["doPresmooth"]
        correct_corners = self.params["correctCorners"]
        # Subtract background
        bs = BackgroundSubtracter()
        # Load the image at index n
        ip = self.stack.getProcessor(n)
        # Fail-safe execution of the filter, which is a global function name
        if self.params["adjustContrast"]:
            try:
                ip = execute_filter(ip, self.params)
            except:
                print(sys.exc_info())
            WaitForUserDialog("Adjust the contrast,then click OK.").show()
            imp = ImagePlus("", ip)
            FileSaver(imp).saveAsTiff(str(self.tiff_contrast_adjusted_no_bg_sub_path.split(".")[0]) + "_" + str(n) +
                                      config.tiff_ext)
            bs.rollingBallBackground(ip, radius, create_background, light_background, use_paraboloid, do_presmooth,
                                     correct_corners)
            imp = ImagePlus("", ip)
            FileSaver(imp).saveAsTiff(str(self.tiff_contrast_adjusted_bg_sub_path.split(".")[0]) + "_" + str(n) +
                                      config.tiff_ext)

        else:
            imp = ImagePlus("", ip)
            WaitForUserDialog("Adjust the area,then click OK.").show()
            FileSaver(imp).saveAsTiff(
                str(self.tiff_no_contrast_adjusted_no_bg_sub_path.split(".")[0]) + "_" + str(n) + config.tiff_ext)
            bs.rollingBallBackground(ip, radius, create_background, light_background, use_paraboloid, do_presmooth,
                                     correct_corners)
            imp = ImagePlus("", ip)
            FileSaver(imp).saveAsTiff(str(self.tiff_no_contrast_adjusted_bg_sub_path.split(".")[0]) + "_" + str(n) +
                                      config.tiff_ext)
        return ip


# Doesn't matter that this function is defined after the class method
# that will invoke it: at run time, this function name will be searched for
# among the existing global variables every time that the getProcessor method
# is invoked, and eventually, when this function is defined, it will find it:
def execute_filter(ip, params):
    """ Given an ImageProcessor ip and a dictionary of parameters, filter the ip,
      and return the same or a new ImageProcessor of the same dimensions and type. """
    block_radius_x = params["blockRadiusX"]
    block_radius_y = params["blockRadiusY"]
    stds = params["stds"]
    center = params["center"]
    stretch = params["stretch"]
    NormalizeLocalContrast.run(ip, block_radius_x, block_radius_y, stds, center, stretch)
    return ip


def ask_for_parameters():
    gui = GenericDialog("Parameter settings")

    gui.addMessage("Background Parameters")

    gui.addNumericField("Radius", 50, 0)  # 0 for no decimal part
    gui.addCheckbox("createBackground", False)
    gui.addCheckbox("lightBackground", False)
    gui.addCheckbox("useParaboloid", False)
    gui.addCheckbox("doPresmooth", False)
    gui.addCheckbox("correctCorners", False)

    gui.addMessage("Contrast Parameters")

    gui.addCheckbox("Adjust Contrast", False)

    gui.addNumericField("Block Radius X", 20)
    gui.addNumericField("Block Radius Y", 20)
    gui.addNumericField("stds", 2, 0)
    gui.addCheckbox("center", False)
    gui.addCheckbox("stretch", False)
    gui.addMessage("Overwrite option")
    gui.addCheckbox("forceSave", False)

    gui.showDialog()

    if gui.wasCanceled():
        IJ.log("User canceled dialog! Doing nothing. Exit")
        return
    params = {
        "radius": gui.getNextNumber(),  # This always return a double (ie might need to cast to int)
        "createBackground": gui.getNextBoolean(),
        "lightBackground": gui.getNextBoolean(),
        "useParaboloid": gui.getNextBoolean(),
        "doPresmooth": gui.getNextBoolean(),
        "correctCorners": gui.getNextBoolean(),
        "adjustContrast": gui.getNextBoolean(),
        "blockRadiusX": int(gui.getNextNumber()),
        "blockRadiusY": int(gui.getNextNumber()),
        "stds": int(gui.getNextNumber()),
        "center": gui.getNextBoolean(),
        "stretch": gui.getNextBoolean(),
        "forceSave": gui.getNextBoolean()
    }
    return params


def main():
    input_dir = config.alignmentDir
    tiff_files = []
    for tiff_file in os.listdir(input_dir):
        if "_Cropped" in os.path.basename(tiff_file) and tiff_file.endswith(config.tiff_ext):
            tiff_files.append(tiff_file)
    try:
        params = ask_for_parameters()
    except:
        # user canceled dialog
        return
    for tiff_file in tiff_files:
        IJ.log(str(tiff_file))
        tiff_contrast_adjusted_no_bg_sub_path = os.path.join(input_dir,
                                                             os.path.basename(tiff_file).split('.')[
                                                                 0] + "_contrast_adjusted_no_bg_sub" +
                                                             config.tiff_ext).replace("\\", "/")
        tiff_no_contrast_adjusted_no_bg_sub_path = os.path.join(input_dir,
                                                                os.path.basename(tiff_file).split('.')[
                                                                    0] + "_no_contrast_adjusted_no_bg_sub" +
                                                                config.tiff_ext).replace("\\", "/")
        tiff_no_contrast_adjusted_bg_sub_path = os.path.join(input_dir,
                                                             os.path.basename(tiff_file).split('.')[
                                                                 0] + "_no_contrast_adjusted_bg_sub" +
                                                             config.tiff_ext).replace("\\", "/")
        tiff_contrast_adjusted_bg_sub_path = os.path.join(input_dir,
                                                          os.path.basename(tiff_file).split('.')[
                                                              0] + "_contrast_adjusted_bg_sub" +
                                                          config.tiff_ext).replace("\\", "/")

        imp = IJ.openImage(os.path.join(input_dir, tiff_file))
        imp.show()
        stack = imp.getStack()
        res = ImagePlus("res", ExtractedImagesFromStack(stack, params, tiff_contrast_adjusted_no_bg_sub_path,
                                                        tiff_no_contrast_adjusted_no_bg_sub_path,
                                                        tiff_no_contrast_adjusted_bg_sub_path,
                                                        tiff_contrast_adjusted_bg_sub_path))
        res.show()
        imp.close()


if __name__ in ['__builtin__', '__main__']:
    main()
