# -*- coding: utf-8 -*-
from ij import VirtualStack

import logging

# im-jy-package.cropped_stack.py creates its own logger, as a sub logger to
# 'multiplex.macro.im-jy-package.main.CROPPING'
logger = logging.getLogger('multiplex.macro.im-jy-package.main.CROPPING.croppedStack')


class CroppedStack(VirtualStack):
    def __init__(self, stack, roi):
        # Constructor: tell the superclass VirtualStack about the dimensions
        super(VirtualStack, self).__init__(stack.getWidth(), stack.getHeight(), stack.size())
        self.cur_stack = stack
        self.cur_region = roi

    def getProcessor(self, n):
        logger.info("processed slice " + str(n))
        # Modify the same slice at index n every time it is requested
        ip = self.cur_stack.getProcessor(n)
        ip.setRoi(self.cur_region)
        return ip.crop()
