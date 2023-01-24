from ij import VirtualStack


class CroppedStack(VirtualStack):
    def __init__(self, stack, roi):
        # Constructor: tell the superclass VirtualStack about the dimensions
        super(VirtualStack, self).__init__(stack.getWidth(), stack.getHeight(), stack.size())
        self.cur_stack = stack
        self.cur_region = roi

    def getProcessor(self, n):
        print("processed slice " + str(n))
        # Modify the same slice at index n every time it is requested
        ip = self.cur_stack.getProcessor(n)
        ip.setRoi(self.cur_region)
        return ip.crop()
