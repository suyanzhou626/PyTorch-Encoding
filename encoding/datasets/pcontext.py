###########################################################################
# Created by: Hang Zhang
# Email: zhang.hang@rutgers.edu
# Copyright (c) 2017
###########################################################################

from PIL import Image, ImageOps, ImageFilter
import os
import os.path
import math
import random
import numpy as np

import torch
from .base import BaseDataset

class ContextSegmentation(BaseDataset):
    BASE_DIR = 'VOCdevkit/VOC2010'
    NUM_CLASS = 59
    def __init__(self, root=os.path.expanduser('~/.encoding/data'), split='train',
                 mode=None, transform=None, target_transform=None):
        super(ContextSegmentation, self).__init__(
            root, split, mode, transform, target_transform)
        from detail import Detail
        #from detail import mask
        root = os.path.join(root, self.BASE_DIR)
        annFile = os.path.join(root, 'trainval_merged.json')
        imgDir = os.path.join(root, 'JPEGImages')
        # training mode
        if split == 'train':
            phase = 'train'
        elif split == 'val':
            phase = 'val'
        elif split == 'test':
            phase = 'val'
            #phase = 'test'
        print('annFile', annFile)
        print('imgDir', imgDir)
        self.detail = Detail(annFile, imgDir, phase)
        self.transform = transform
        self.target_transform = target_transform
        self.ids = self.detail.getImgs()
        self._mapping = np.sort(np.array([
            0, 2, 259, 260, 415, 324, 9, 258, 144, 18, 19, 22, 
            23, 397, 25, 284, 158, 159, 416, 33, 162, 420, 454, 295, 296, 
            427, 44, 45, 46, 308, 59, 440, 445, 31, 232, 65, 354, 424, 
            68, 326, 72, 458, 34, 207, 80, 355, 85, 347, 220, 349, 360, 
            98, 187, 104, 105, 366, 189, 368, 113, 115]))
        self._key = np.array(range(len(self._mapping))).astype('uint8')

    def _class_to_index(self, mask):
        # assert the values
        values = np.unique(mask)
        #assert(values.size > 1)
        for i in range(len(values)):
            assert(values[i] in self._mapping)
        index = np.digitize(mask.ravel(), self._mapping, right=True)
        return self._key[index].reshape(mask.shape)

    def __getitem__(self, index):
        detail = self.detail
        img_id = self.ids[index]
        path = img_id['file_name']
        iid = img_id['image_id']
        img = Image.open(os.path.join(detail.img_folder, path)).convert('RGB')
        if self.mode == 'test':
            if self.transform is not None:
                img = self.transform(img)
            return img, os.path.basename(path)
        # convert mask to 60 categories
        mask = Image.fromarray(self._class_to_index(
            detail.getMask(img_id)))
        # synchrosized transform
        if self.mode == 'train':
            img, mask = self._sync_transform(img, mask)
        elif self.mode == 'val':
            img, mask = self._val_sync_transform(img, mask)
        else:
            assert self.mode == 'testval'
            mask = self._mask_transform(mask)
        # general resize, normalize and toTensor
        if self.transform is not None:
            #print("transform for input")
            img = self.transform(img)
        if self.target_transform is not None:
            #print("transform for label")
            mask = self.target_transform(mask)
        return img, mask

    def _mask_transform(self, mask):
        target = np.array(mask).astype('int32') - 1
        return torch.from_numpy(target).long()

    def __len__(self):
        return len(self.ids)

    @property
    def pred_offset(self):
        return 1
