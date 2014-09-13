#!/usr/bin/python -u
# vim: ai et fileencoding=utf-8 ts=4 sw=4:

import re, sys, urllib, urllib2, cookielib
import Image, ImageFilter

# Peel off background, Const Table
Delta = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
sur_d = [[-1, 0], [1, 0], [0, -1], [0, 1]]
background = {}
blocks, index, band, bands, code  = set(), {}, {}, {}, {}
# Recognize, Const Table
alphabet = list("ABCDEFGHIJKLMNOPQ0RSTUVWXYZ123456789ABCDEFGHIJKLMNOPQ0RSTUVWXYZ123456789")
chars = {}

# Load all backgrounds
def init_background():
    global background
    for i in range(7):
        background[i] = Image.open("background/" + str(i+1) + ".jpg")
        # print background[i].getpixel((0, 39))

# Get this Authcode's background by comparing pixel_A with pixel_B
def get_background():
    count = [[0, i] for i in range(7)]
    for k in range(9):
        pixel = (k*15, 0)
        for i in range(7):
            RGB = background[i].getpixel(pixel)
            color = code.getpixel(pixel)
            Do = True
            for j in range(3):
                if abs(RGB[j] - color[j]) > 10:
                    Do = False
                    break
            if Do:
                count[i][0] += 1
    count = sorted(count, cmp=lambda x, y:cmp(y[0], x[0]))
    return count[0][1]
  
# Peel off this Authcode's background by comparing pixel_A with pixel_B
def peel_off_background():
    global code
    for x in range(code.size[0]):
        for y in range(code.size[1]):
            Deritive = 0
            for d in range(3):
                Deritive += abs(code.getpixel((x, y))[d] - temp.getpixel((x, y))[d])
            if Deritive < 30:
                code.putpixel((x, y), (255, 255, 255))

class bg1:
    # Fill in some pixels by this surrounding pixels
    def mend_image(self, pixels, g, x, y):
        sur = [0, 0, 0, 0]
        for cur in range(4):
            sur[cur] = pixels[x + sur_d[cur][0], y + sur_d[cur][1]]
        if sur[0] == sur[1] == 0 or sur[2] == sur[3] == 0:
            g.putpixel((x, y), 0)
        if y+2 < g.size[1] and sur[2] == pixels[x, y+2] == 0 and sur[3] == 255:
            g.putpixel((x, y), 0)
         
    # Check up the pixel is or not in image 
    def mend_is_legal(self, pixel1, pixel2, color):
        #print pixel1, pixel2
        return pixel1[0] > 1 and pixel1[0] < pixel2[0] and pixel1[1] > 1 and pixel1[1] < pixel2[1] and color == 255

    # Use DFS to peel off isolated pixels
    def DFS(self):
        global band, blocks, index
        def dfs(pixel, block_id):
            if pixel[0] < 0 or pixel[0] >= band.size[0] \
                    or pixel[1] < 0 or pixel[1] >= band.size[1]:
                return
            if pixels[pixel] == 255 or pixel in vis:
                return
            vis.add(pixel)
            index[pixel] = block_id
            for k in range(8):
                dfs((pixel[0]+Delta[k][0], pixel[1]+Delta[k][1]), block_id)

        pixels = band.load()
        vis, q, index, block_id = set(), [], {}, 0
        q.append((0, 0))
        count = [[0, k] for k in range(100)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if not(pixel in vis) and pixels[pixel] == 0:
                    block_id += 1
                    dfs(pixel, block_id)
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if pixels[(x, y)] == 0:
                    count[index[(x, y)]][0] += 1
        count = sorted(count, cmp=lambda x,y:cmp(y[0],x[0]))
        blocks = set()
        for i in range(4):
            blocks.add(count[i][1])
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[pixel] == 0 and (not index[pixel] in blocks):
                    band.putpixel(pixel, 255)

    # Peel off this Authcode's background and noises, and change this image into black-and-white image
    def init_background(self, code, temp, icode=0):
        global band, blocks, index
        #peel_off_background()
        #code = code.filter(ImageFilter.DETAIL)
        bands = list(code.split())
        for i in range(3):
            bands[i] = bands[i].point(lambda i: i * 1.5)
            #bands[i].save("codeL_"+str(i)+".png")
        bands[0] = bands[0].point(lambda i: 255-i)
        band = bands[0]

        # Remove the noises by paramter
        pixels = band.load()
        count = [[0, i] for i in range(256)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                count[pixels[x, y]][0] += 1
        count = sorted(count, cmp=lambda x,y:cmp(y[0],x[0]))
        """
        for i in range(26):
            if count[i][0] <= 10:
                break
            print "Color " + str(i) + " is", count[i][0], 10*count[i][1]
        """

        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if pixels[x, y] > 11:
                    band.putpixel((x, y), 255)
                else:
                    band.putpixel((x, y), 0)
        
        # Mend the image, such as holes made by noises
        pixels = band.load()
        for X in range(band.size[0]):
            for Y in range(band.size[1]):
                x, y = band.size[0]-X-1, band.size[1]-Y-1
                key = pixels[x, y]
                if self.mend_is_legal((x+1, y+1), band.size, key):
                    self.mend_image(pixels, band, x, y)

        # Remove other noises by DFS, such as circle and isolate point
        blocks, index = set(), {}
        self.DFS()
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[x, y] == 0 and x > 0 and x+1 < band.size[0] and y > 0 and y+1 < band.size[1]:
                    if (int(pixels[x-1,y] == 255) + int(pixels[x+1,y] == 255) + \
                            int(pixels[x,y-1] == 255) + int(pixels[x,y+1] == 255) >= 3) \
                            or pixels[x-1,y] == pixels[x+1,y] == 255\
                            or pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)
                    if pixels[x-1,y] == pixels[x+1,y] == 255 or\
                            pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[x, y] == 0 and x > 1 and x+2 < band.size[0] and y > 1 and y+2 < band.size[1]:
                    if (pixels[x-1,y] == pixels[x+2,y] == 255 and pixels[x+1,y] == 0) or\
                            (pixels[x,y-1] == pixels[x,y+2] == 255 and pixels[x,y+1] == 0):
                        band.putpixel(pixel, 255)
                if pixels[x, y] == 0 and x > 0 and x+1 < band.size[0] and y > 0 and y+1 < band.size[1]:
                    if pixels[x-1,y] == pixels[x+1,y] == 255 or\
                            pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)

        self.DFS()


        # Split the image
        blocks = list(blocks)
        boundary = [[150, 40, 0, 0] for k in range(4)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if not (x, y) in index:
                    continue
                idx = index[x, y]
                for k in range(4):
                    if idx == blocks[k]:
                        boundary[k][0] = min(boundary[k][0], x)
                        boundary[k][1] = min(boundary[k][1], y)
                        boundary[k][2] = max(boundary[k][2], x)
                        boundary[k][3] = max(boundary[k][3], y)
                        break
        part = {}
        characters = 0
        boundary = sorted(boundary, cmp = lambda x, y:cmp(x[0], y[0]))
        for k in range(4):
            part[k] = band.crop(tuple(boundary[k]))
            #part[k].show()
            #print boundary[k]
            #print part[k]
            if boundary[k][0] < boundary[k][2] and boundary[k][1] < boundary[k][3]:
                part[k].save(str(icode*4+k)+".png")
                characters += 1
        
        if characters == 4:
            return True
        else:
            return False

class bg2:
    # Fill in some pixels by this surrounding pixels
    def mend_image(self, pixels, g, noise1, noise2, x, y):
        sur = [0, 0, 0, 0]
        for cur in range(4):
            sur[cur] = pixels[x + sur_d[cur][0], y + sur_d[cur][1]]
        if (sur[0] == sur[1] == 0 or sur[2] == sur[3] == 0) and (noise2[x, y] < 250):
            g.putpixel((x, y), 0)
        if y+2 < g.size[1] and sur[2] == pixels[x, y+2] == 0 and sur[3] == 255 and (noise2[x, y] < 240):
            g.putpixel((x, y), 0)
         
    # Check up the pixel is or not in image 
    def mend_is_legal(self, pixel1, pixel2, color):
        #print pixel1, pixel2
        return pixel1[0] > 1 and pixel1[0] < pixel2[0] and pixel1[1] > 1 and pixel1[1] < pixel2[1] and color == 255

    # Use DFS to peel off isolated pixels
    def DFS(self):
        global band, blocks, index
        def dfs(pixel, block_id):
            if pixel[0] < 0 or pixel[0] >= band.size[0] \
                    or pixel[1] < 0 or pixel[1] >= band.size[1]:
                return
            if pixels[pixel] == 255 or pixel in vis:
                return
            vis.add(pixel)
            index[pixel] = block_id
            for k in range(8):
                dfs((pixel[0]+Delta[k][0], pixel[1]+Delta[k][1]), block_id)

        pixels = band.load()
        vis, q, index, block_id = set(), [], {}, 0
        q.append((0, 0))
        count = [[0, k] for k in range(100)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if not(pixel in vis) and pixels[pixel] == 0:
                    block_id += 1
                    dfs(pixel, block_id)
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if pixels[(x, y)] == 0:
                    count[index[(x, y)]][0] += 1
        count = sorted(count, cmp=lambda x,y:cmp(y[0],x[0]))
        blocks = set()
        for i in range(4):
            blocks.add(count[i][1])
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[pixel] == 0 and (not index[pixel] in blocks):
                    band.putpixel(pixel, 255)

    # Peel off this Authcode's background and noises, and change this image into black-and-white image
    def init_background(self, code, temp, icode=0):
        global band, blocks, index
        peel_off_background()
        #code = code.filter(ImageFilter.DETAIL)
        bands = list(code.split())
        for i in range(3):
            bands[i] = bands[i].point(lambda i: i * 1.2)
            #bands[i].save("codeL_"+str(i)+".png")
        band = bands[1]
        for i in range(3):
            bands[i] = bands[i].load()

        # Remove the noises by paramter
        pixels = band.load()
        count = [[0, i] for i in range(256)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                count[pixels[x, y] // 10][0] += 1
        count = sorted(count, cmp=lambda x,y:cmp(y[0],x[0]))
        """
        for i in range(26):
            if count[i][0] <= 10:
                break
            print "Color " + str(i) + " is", count[i][0], 10*count[i][1]
        """
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if pixels[x, y] > 200:
                    band.putpixel((x, y), 255)
                else:
                    band.putpixel((x, y), 0)
        
        # Mend the image, such as holes made by noises
        pixels = band.load()
        for X in range(band.size[0]):
            for Y in range(band.size[1]):
                x, y = band.size[0]-X-1, band.size[1]-Y-1
                key = pixels[x, y]
                if self.mend_is_legal((x+1, y+1), band.size, key):
                    self.mend_image(pixels, band, bands[0], bands[2], x, y)

        pixels = band.load()
        for X in range(band.size[0]):
            for Y in range(band.size[1]):
                x, y = band.size[0]-X-1, band.size[1]-Y-1
                key = pixels[x, y]
                if self.mend_is_legal((x+1, y+1), band.size, key):
                    self.mend_image(pixels, band, bands[0], bands[2], x, y)

        # Remove other noises by DFS, such as circle and isolate point
        blocks, index = set(), {}
        pixels = band.load()
        self.DFS()
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[x, y] == 0 and x > 0 and x+1 < band.size[0] and y > 0 and y+1 < band.size[1]:
                    if (int(pixels[x-1,y] == 255) + int(pixels[x+1,y] == 255) + \
                            int(pixels[x,y-1] == 255) + int(pixels[x,y+1] == 255) >= 3) \
                            or pixels[x-1,y] == pixels[x+1,y] == 255\
                            or pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)
                    if pixels[x-1,y] == pixels[x+1,y] == 255 or\
                            pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[x, y] == 0 and x > 1 and x+2 < band.size[0] and y > 1 and y+2 < band.size[1]:
                    if (pixels[x-1,y] == pixels[x+2,y] == 255 and pixels[x+1,y] == 0) or\
                            (pixels[x,y-1] == pixels[x,y+2] == 255 and pixels[x,y+1] == 0):
                        band.putpixel(pixel, 255)
                if pixels[x, y] == 0 and x > 0 and x+1 < band.size[0] and y > 0 and y+1 < band.size[1]:
                    if pixels[x-1,y] == pixels[x+1,y] == 255 or\
                            pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)

        self.DFS()

        # Split the image
        blocks = list(blocks)
        boundary = [[150, 40, 0, 0] for k in range(4)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if not (x, y) in index:
                    continue
                idx = index[x, y]
                for k in range(4):
                    if idx == blocks[k]:
                        boundary[k][0] = min(boundary[k][0], x)
                        boundary[k][1] = min(boundary[k][1], y)
                        boundary[k][2] = max(boundary[k][2], x)
                        boundary[k][3] = max(boundary[k][3], y)
                        break
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if bands[2][x, y] > 135:
                    band.putpixel((x, y), 255)
        part = {}
        characters = 0
        boundary = sorted(boundary, cmp=lambda x, y:cmp(x[0], y[0]))
        for k in range(4):
            part[k] = band.crop(tuple(boundary[k]))
            #part[k].show()
            #print boundary[k]
            #print part[k]
            if boundary[k][0] < boundary[k][2] and boundary[k][1] < boundary[k][3]:
                part[k].save(str(icode*4+k)+".png")
                characters += 1
        
        #band.show();band.save("codeR.png");sys.exit()
        if characters == 4:
            return True
        else:
            return False

class bg3:
    # Fill in some pixels by this surrounding pixels
    def mend_image(self, pixels, g, noise1, noise2, x, y):
        sur = [0, 0, 0, 0]
        for cur in range(4):
            sur[cur] = pixels[x + sur_d[cur][0], y + sur_d[cur][1]]
        if (sur[0] == sur[1] == 0 or sur[2] == sur[3] == 0):
            #and (noise1[x, y] != 255 or noise2[x, y] != 255 or pixels[x, y] != 255):
            g.putpixel((x, y), 0)
        if y+2 < g.size[1] and sur[2] == pixels[x, y+2] == 0 and sur[3] == 255:
            #and (noise1[x, y] != 255 or noise2[x, y] != 255 or pixels[x, y] != 255):
            g.putpixel((x, y), 0)
         
    # Check up the pixel is or not in image 
    def mend_is_legal(self, pixel1, pixel2, color):
        #print pixel1, pixel2
        return pixel1[0] > 1 and pixel1[0] < pixel2[0] and pixel1[1] > 1 and pixel1[1] < pixel2[1] and color == 255

    # Use DFS to peel off isolated pixels
    def DFS(self):
        global band, blocks, index
        def dfs(pixel, block_id):
            if pixel[0] < 0 or pixel[0] >= band.size[0] \
                    or pixel[1] < 0 or pixel[1] >= band.size[1]:
                return
            if pixels[pixel] == 255 or pixel in vis:
                return
            vis.add(pixel)
            index[pixel] = block_id
            for k in range(8):
                dfs((pixel[0]+Delta[k][0], pixel[1]+Delta[k][1]), block_id)

        pixels = band.load()
        vis, q, index, block_id = set(), [], {}, 0
        q.append((0, 0))
        count = [[0, k] for k in range(100)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if not(pixel in vis) and pixels[pixel] == 0:
                    block_id += 1
                    dfs(pixel, block_id)
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if pixels[(x, y)] == 0:
                    count[index[(x, y)]][0] += 1
        count = sorted(count, cmp=lambda x,y:cmp(y[0],x[0]))
        blocks = set()
        for i in range(4):
            blocks.add(count[i][1])
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[pixel] == 0 and (not index[pixel] in blocks):
                    band.putpixel(pixel, 255)

    # Peel off this Authcode's background and noises, and change this image into black-and-white image
    def init_background(self, code, temp, icode=0):
        global band, blocks, index
        peel_off_background()
        #code = code.filter(ImageFilter.DETAIL)
        bands = list(code.split())
        for i in range(3):
            bands[i] = bands[i].point(lambda i: i*1.5)
            #bands[i].save("codeL_"+str(i)+".png")
        #bands[1] = bands[1].point(lambda i: 255-i)
        band = bands[1]
        for i in range(3):
            bands[i] = bands[i].load()

        # Remove the noises by paramter
        pixels = band.load()
        count = [[0, i] for i in range(256)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                count[pixels[x, y] // 10][0] += 1
        count = sorted(count, cmp=lambda x,y:cmp(y[0],x[0]))
        """
        for i in range(26):
            if count[i][0] <= 10:
                break
            print "Color " + str(i) + " is", count[i][0], 10*count[i][1]
        """
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if 100 < pixels[x, y] < 180:
                    band.putpixel((x, y), 0)
                else:
                    band.putpixel((x, y), 255)
        
        # Mend the image, such as holes made by noises
        pixels = band.load()
        for X in range(band.size[0]):
            for Y in range(band.size[1]):
                x, y = band.size[0]-X-1, band.size[1]-Y-1
                key = pixels[x, y]
                if self.mend_is_legal((x+1, y+1), band.size, key):
                    self.mend_image(pixels, band, bands[0], bands[2], x, y)

        pixels = band.load()
        for X in range(band.size[0]):
            for Y in range(band.size[1]):
                x, y = band.size[0]-X-1, band.size[1]-Y-1
                key = pixels[x, y]
                if self.mend_is_legal((x+1, y+1), band.size, key):
                    self.mend_image(pixels, band, bands[0], bands[2], x, y)

        # Remove other noises by DFS, such as circle and isolate point
        blocks, index = set(), {}
        pixels = band.load()
        self.DFS()
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[x, y] == 0 and x > 0 and x+1 < band.size[0] and y > 0 and y+1 < band.size[1]:
                    if (int(pixels[x-1,y] == 255) + int(pixels[x+1,y] == 255) + \
                            int(pixels[x,y-1] == 255) + int(pixels[x,y+1] == 255) >= 3) \
                            or pixels[x-1,y] == pixels[x+1,y] == 255\
                            or pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)
                    if pixels[x-1,y] == pixels[x+1,y] == 255 or\
                            pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)
        """
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[x, y] == 0 and x > 1 and x+2 < band.size[0] and y > 1 and y+2 < band.size[1]:
                    if (pixels[x-1,y] == pixels[x+2,y] == 255 and pixels[x+1,y] == 0) or\
                            (pixels[x,y-1] == pixels[x,y+2] == 255 and pixels[x,y+1] == 0):
                        band.putpixel(pixel, 255)
                if pixels[x, y] == 0 and x > 0 and x+1 < band.size[0] and y > 0 and y+1 < band.size[1]:
                    if pixels[x-1,y] == pixels[x+1,y] == 255 or\
                            pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)
"""
        self.DFS()

        # Split the image
        blocks = list(blocks)
        boundary = [[150, 40, 0, 0] for k in range(4)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if not (x, y) in index:
                    continue
                idx = index[x, y]
                for k in range(4):
                    if idx == blocks[k]:
                        boundary[k][0] = min(boundary[k][0], x)
                        boundary[k][1] = min(boundary[k][1], y)
                        boundary[k][2] = max(boundary[k][2], x)
                        boundary[k][3] = max(boundary[k][3], y)
                        break
        part = {}
        characters = 0
        boundary = sorted(boundary, cmp=lambda x, y:cmp(x[0], y[0]))
        for k in range(4):
            part[k] = band.crop(tuple(boundary[k]))
            #part[k].show()
            #print boundary[k]
            #print part[k]
            if boundary[k][0] < boundary[k][2] and boundary[k][1] < boundary[k][3]:
                part[k].save(str(icode*4+k)+".png")
                characters += 1
        
        #band.show();band.save("codeR.png");sys.exit()
        if characters == 4:
            return True
        else:
            return False

class bg4:
    # Fill in some pixels by this surrounding pixels
    def mend_image(self, pixels, g, noise1, noise2, x, y):
        sur = [0, 0, 0, 0]
        for cur in range(4):
            sur[cur] = pixels[x + sur_d[cur][0], y + sur_d[cur][1]]
        if (sur[0] == sur[1] == 0 or sur[2] == sur[3] == 0) and (noise1[x, y] != 255 or noise2[x, y] != 255 or pixels[x, y] != 255):
            g.putpixel((x, y), 0)
        if y+2 < g.size[1] and sur[2] == pixels[x, y+2] == 0 and sur[3] == 255 and (noise1[x, y] != 255 or noise2[x, y] != 255 or pixels[x, y] != 255):
            g.putpixel((x, y), 0)
         
    # Check up the pixel is or not in image 
    def mend_is_legal(self, pixel1, pixel2, color):
        #print pixel1, pixel2
        return pixel1[0] > 1 and pixel1[0] < pixel2[0] and pixel1[1] > 1 and pixel1[1] < pixel2[1] and color == 255

    # Use DFS to peel off isolated pixels
    def DFS(self):
        global band, blocks, index
        def dfs(pixel, block_id):
            if pixel[0] < 0 or pixel[0] >= band.size[0] \
                    or pixel[1] < 0 or pixel[1] >= band.size[1]:
                return
            if pixels[pixel] == 255 or pixel in vis:
                return
            vis.add(pixel)
            index[pixel] = block_id
            for k in range(8):
                dfs((pixel[0]+Delta[k][0], pixel[1]+Delta[k][1]), block_id)

        pixels = band.load()
        vis, q, index, block_id = set(), [], {}, 0
        q.append((0, 0))
        count = [[0, k] for k in range(100)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if not(pixel in vis) and pixels[pixel] == 0:
                    block_id += 1
                    dfs(pixel, block_id)
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if pixels[(x, y)] == 0:
                    count[index[(x, y)]][0] += 1
        count = sorted(count, cmp=lambda x,y:cmp(y[0],x[0]))
        blocks = set()
        for i in range(4):
            blocks.add(count[i][1])
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[pixel] == 0 and (not index[pixel] in blocks):
                    band.putpixel(pixel, 255)

    # Peel off this Authcode's background and noises, and change this image into black-and-white image
    def init_background(self, code, temp, icode=0):
        global band, blocks, index
        peel_off_background()
        #code = code.filter(ImageFilter.DETAIL)
        bands = list(code.split())
        for i in range(3):
            bands[i] = bands[i].point(lambda i: i * 1.5)
            #bands[i].save("codeL_"+str(i)+".png")
        #bands[0] = bands[0].point(lambda i: 255-i)
        band = bands[1]
        for i in range(3):
            bands[i] = bands[i].load()

        # Remove the noises by paramter
        pixels = band.load()
        count = [[0, i] for i in range(256)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                count[pixels[x, y] // 10][0] += 1
        count = sorted(count, cmp=lambda x,y:cmp(y[0],x[0]))
        """
        for i in range(26):
            if count[i][0] <= 10:
                break
            print "Color " + str(i) + " is", count[i][0], 10*count[i][1]
        """
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if pixels[x, y] > 200:
                    band.putpixel((x, y), 255)
                else:
                    band.putpixel((x, y), 0)
        
        # Mend the image, such as holes made by noises
        pixels = band.load()
        for X in range(band.size[0]):
            for Y in range(band.size[1]):
                x, y = band.size[0]-X-1, band.size[1]-Y-1
                key = pixels[x, y]
                if self.mend_is_legal((x+1, y+1), band.size, key):
                    self.mend_image(pixels, band, bands[0], bands[2], x, y)

        pixels = band.load()
        for X in range(band.size[0]):
            for Y in range(band.size[1]):
                x, y = band.size[0]-X-1, band.size[1]-Y-1
                key = pixels[x, y]
                if self.mend_is_legal((x+1, y+1), band.size, key):
                    self.mend_image(pixels, band, bands[0], bands[2], x, y)

        # Remove other noises by DFS, such as circle and isolate point
        blocks, index = set(), {}
        pixels = band.load()
        self.DFS()
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[x, y] == 0 and x > 0 and x+1 < band.size[0] and y > 0 and y+1 < band.size[1] and (bands[0][x, y] == 255 or bands[2][x, y] == 255 or pixels[x, y] == 255):
                    if (int(pixels[x-1,y] == 255) + int(pixels[x+1,y] == 255) + \
                            int(pixels[x,y-1] == 255) + int(pixels[x,y+1] == 255) >= 3) \
                            or pixels[x-1,y] == pixels[x+1,y] == 255\
                            or pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)
                    if pixels[x-1,y] == pixels[x+1,y] == 255 or\
                            pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[x, y] == 0 and x > 1 and x+2 < band.size[0] and y > 1 and y+2 < band.size[1] and (bands[0][x, y] == 255 or bands[2][x, y] == 255 or pixels[x, y] == 255):
                    if (pixels[x-1,y] == pixels[x+2,y] == 255 and pixels[x+1,y] == 0) or\
                            (pixels[x,y-1] == pixels[x,y+2] == 255 and pixels[x,y+1] == 0):
                        band.putpixel(pixel, 255)
                if pixels[x, y] == 0 and x > 0 and x+1 < band.size[0] and y > 0 and y+1 < band.size[1] and (bands[0][x, y] == 255 or bands[2][x, y] == 255 or pixels[x, y] == 255):
                    if pixels[x-1,y] == pixels[x+1,y] == 255 or\
                            pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)

        self.DFS()

        # Split the image
        blocks = list(blocks)
        boundary = [[150, 40, 0, 0] for k in range(4)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if not (x, y) in index:
                    continue
                idx = index[x, y]
                for k in range(4):
                    if idx == blocks[k]:
                        boundary[k][0] = min(boundary[k][0], x)
                        boundary[k][1] = min(boundary[k][1], y)
                        boundary[k][2] = max(boundary[k][2], x)
                        boundary[k][3] = max(boundary[k][3], y)
                        break
        part = {}
        characters = 0
        boundary = sorted(boundary, cmp=lambda x, y:cmp(x[0], y[0]))
        for k in range(4):
            part[k] = band.crop(tuple(boundary[k]))
            #part[k].show()
            #print boundary[k]
            #print part[k]
            if boundary[k][0] < boundary[k][2] and boundary[k][1] < boundary[k][3]:
                part[k].save(str(icode*4+k)+".png")
                characters += 1
        
        #band.show();band.save("codeR.png");sys.exit()
        if characters == 4:
            return True
        else:
            return False

class bg5:
    # Fill in some pixels by this surrounding pixels
    def mend_image(self, pixels, g, noise1, noise2, x, y):
        sur = [0, 0, 0, 0]
        for cur in range(4):
            sur[cur] = pixels[x + sur_d[cur][0], y + sur_d[cur][1]]
        if (sur[0] == sur[1] == 0 or sur[2] == sur[3] == 0) and (noise1[x, y] != 255 or noise2[x, y] != 255 or pixels[x, y] != 255):
            g.putpixel((x, y), 0)
        if y+2 < g.size[1] and sur[2] == pixels[x, y+2] == 0 and sur[3] == 255 and (noise1[x, y] != 255 or noise2[x, y] != 255 or pixels[x, y] != 255):
            g.putpixel((x, y), 0)
         
    # Check up the pixel is or not in image 
    def mend_is_legal(self, pixel1, pixel2, color):
        #print pixel1, pixel2
        return pixel1[0] > 1 and pixel1[0] < pixel2[0] and pixel1[1] > 1 and pixel1[1] < pixel2[1] and color == 255

    # Use DFS to peel off isolated pixels
    def DFS(self):
        global band, blocks, index
        def dfs(pixel, block_id):
            if pixel[0] < 0 or pixel[0] >= band.size[0] \
                    or pixel[1] < 0 or pixel[1] >= band.size[1]:
                return
            if pixels[pixel] == 255 or pixel in vis:
                return
            vis.add(pixel)
            index[pixel] = block_id
            for k in range(8):
                dfs((pixel[0]+Delta[k][0], pixel[1]+Delta[k][1]), block_id)

        pixels = band.load()
        vis, q, index, block_id = set(), [], {}, 0
        q.append((0, 0))
        count = [[0, k] for k in range(100)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if not(pixel in vis) and pixels[pixel] == 0:
                    block_id += 1
                    dfs(pixel, block_id)
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if pixels[(x, y)] == 0:
                    count[index[(x, y)]][0] += 1
        count = sorted(count, cmp=lambda x,y:cmp(y[0],x[0]))
        blocks = set()
        for i in range(4):
            blocks.add(count[i][1])
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[pixel] == 0 and (not index[pixel] in blocks):
                    band.putpixel(pixel, 255)

    # Peel off this Authcode's background and noises, and change this image into black-and-white image
    def init_background(self, code, temp, icode=0):
        global band, blocks, index
        #peel_off_background()
        #code = code.filter(ImageFilter.DETAIL)
        bands = list(code.split())
        for i in range(3):
            bands[i] = bands[i].point(lambda i: i)
            #bands[i].save("codeL_"+str(i)+".png")
        bands[1] = bands[1].point(lambda i: 255-i)
        band = bands[1]
        for i in range(3):
            bands[i] = bands[i].load()

        # Remove the noises by paramter
        pixels = band.load()
        count = [[0, i] for i in range(256)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                count[pixels[x, y] // 10][0] += 1
        count = sorted(count, cmp=lambda x,y:cmp(y[0],x[0]))
        """
        for i in range(26):
            if count[i][0] <= 10:
                break
            print "Color " + str(i) + " is", count[i][0], 10*count[i][1]
        """
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if pixels[x, y] > 20:
                    band.putpixel((x, y), 255)
                else:
                    band.putpixel((x, y), 0)
        
        # Mend the image, such as holes made by noises
        pixels = band.load()
        for X in range(band.size[0]):
            for Y in range(band.size[1]):
                x, y = band.size[0]-X-1, band.size[1]-Y-1
                key = pixels[x, y]
                if self.mend_is_legal((x+1, y+1), band.size, key):
                    self.mend_image(pixels, band, bands[0], bands[2], x, y)

        pixels = band.load()
        for X in range(band.size[0]):
            for Y in range(band.size[1]):
                x, y = band.size[0]-X-1, band.size[1]-Y-1
                key = pixels[x, y]
                if self.mend_is_legal((x+1, y+1), band.size, key):
                    self.mend_image(pixels, band, bands[0], bands[2], x, y)

        # Remove other noises by DFS, such as circle and isolate point
        blocks, index = set(), {}
        pixels = band.load()
        self.DFS()
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[x, y] == 0 and x > 0 and x+1 < band.size[0] and y > 0 and y+1 < band.size[1]:
                    if (int(pixels[x-1,y] == 255) + int(pixels[x+1,y] == 255) + \
                            int(pixels[x,y-1] == 255) + int(pixels[x,y+1] == 255) >= 3) \
                            or pixels[x-1,y] == pixels[x+1,y] == 255\
                            or pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)
                    if pixels[x-1,y] == pixels[x+1,y] == 255 or\
                            pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[x, y] == 0 and x > 1 and x+2 < band.size[0] and y > 1 and y+2 < band.size[1]:
                    if (pixels[x-1,y] == pixels[x+2,y] == 255 and pixels[x+1,y] == 0) or\
                            (pixels[x,y-1] == pixels[x,y+2] == 255 and pixels[x,y+1] == 0):
                        band.putpixel(pixel, 255)
                if pixels[x, y] == 0 and x > 0 and x+1 < band.size[0] and y > 0 and y+1 < band.size[1]:
                    if pixels[x-1,y] == pixels[x+1,y] == 255 or\
                            pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)

        self.DFS()

        # Split the image
        blocks = list(blocks)
        boundary = [[150, 40, 0, 0] for k in range(4)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if not (x, y) in index:
                    continue
                idx = index[x, y]
                for k in range(4):
                    if idx == blocks[k]:
                        boundary[k][0] = min(boundary[k][0], x)
                        boundary[k][1] = min(boundary[k][1], y)
                        boundary[k][2] = max(boundary[k][2], x)
                        boundary[k][3] = max(boundary[k][3], y)
                        break
        part = {}
        characters = 0
        boundary = sorted(boundary, cmp=lambda x, y:cmp(x[0], y[0]))
        for k in range(4):
            part[k] = band.crop(tuple(boundary[k]))
            #part[k].show()
            #print boundary[k]
            #print part[k]
            if boundary[k][0] < boundary[k][2] and boundary[k][1] < boundary[k][3]:
                part[k].save(str(icode*4+k)+".png")
                characters += 1
        
        #band.show();band.save("codeR.png");sys.exit()
        if characters == 4:
            return True
        else:
            return False

class bg6:
    # Fill in some pixels by this surrounding pixels
    def mend_image(self, pixels, g, noise1, noise2, x, y):
        sur = [0, 0, 0, 0]
        for cur in range(4):
            sur[cur] = pixels[x + sur_d[cur][0], y + sur_d[cur][1]]
        if (sur[0] == sur[1] == 0 or sur[2] == sur[3] == 0) and (noise1[x, y] != 255 or noise2[x, y] != 255 or pixels[x, y] != 255):
            g.putpixel((x, y), 0)
        if y+2 < g.size[1] and sur[2] == pixels[x, y+2] == 0 and sur[3] == 255 and (noise1[x, y] != 255 or noise2[x, y] != 255 or pixels[x, y] != 255):
            g.putpixel((x, y), 0)
             
    # Check up the pixel is or not in image 
    def mend_is_legal(self, pixel1, pixel2, color):
        #print pixel1, pixel2
        return pixel1[0] > 1 and pixel1[0] < pixel2[0] and pixel1[1] > 1 and pixel1[1] < pixel2[1] and color == 255

    # Use DFS to peel off isolated pixels
    def DFS(self):
        global band, blocks, index
        def dfs(pixel, block_id):
            if pixel[0] < 0 or pixel[0] >= band.size[0] \
                    or pixel[1] < 0 or pixel[1] >= band.size[1]:
                return
            if pixels[pixel] == 255 or pixel in vis:
                return
            vis.add(pixel)
            index[pixel] = block_id
            for k in range(8):
                dfs((pixel[0]+Delta[k][0], pixel[1]+Delta[k][1]), block_id)

        pixels = band.load()
        vis, q, index, block_id = set(), [], {}, 0
        q.append((0, 0))
        count = [[0, k] for k in range(100)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if not(pixel in vis) and pixels[pixel] == 0:
                    block_id += 1
                    dfs(pixel, block_id)
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if pixels[(x, y)] == 0:
                    count[index[(x, y)]][0] += 1
        count = sorted(count, cmp=lambda x,y:cmp(y[0],x[0]))
        blocks = set()
        for i in range(4):
            blocks.add(count[i][1])
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[pixel] == 0 and (not index[pixel] in blocks):
                    band.putpixel(pixel, 255)

    # Peel off this Authcode's background and noises, and change this image into black-and-white image
    def init_background(self, code, temp, icode=0):
        global band, blocks, index
        #peel_off_background()
        #code = code.filter(ImageFilter.DETAIL)
        bands = list(code.split())
        for i in range(3):
            bands[i] = bands[i].point(lambda i: i)
            #bands[i].save("codeL_"+str(i)+".png")
        #bands[1] = bands[1].point(lambda i: 255-i)
        band = bands[0]
        for i in range(3):
            bands[i] = bands[i].load()

        # Remove the noises by paramter
        pixels = band.load()
        count = [[0, i] for i in range(256)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                count[pixels[x, y]//10][0] += 1
        count = sorted(count, cmp=lambda x,y:cmp(y[0],x[0]))
        """
        for i in range(26):
            if count[i][0] <= 10:
                break
            print "Color " + str(i) + " is", count[i][0], 10*count[i][1]
        """
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if 180 < pixels[x, y] < 210:
                    band.putpixel((x, y), 0)
                else:
                    band.putpixel((x, y), 255)
        
        # Mend the image, such as holes made by noises
        pixels = band.load()
        for X in range(band.size[0]):
            for Y in range(band.size[1]):
                x, y = band.size[0]-X-1, band.size[1]-Y-1
                key = pixels[x, y]
                if self.mend_is_legal((x+1, y+1), band.size, key):
                    self.mend_image(pixels, band, bands[0], bands[2], x, y)

        pixels = band.load()
        for X in range(band.size[0]):
            for Y in range(band.size[1]):
                x, y = band.size[0]-X-1, band.size[1]-Y-1
                key = pixels[x, y]
                if self.mend_is_legal((x+1, y+1), band.size, key):
                    self.mend_image(pixels, band, bands[0], bands[2], x, y)

        # Remove other noises by DFS, such as circle and isolate point
        blocks, index = set(), {}
        pixels = band.load()
        self.DFS()
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[x, y] == 0 and x > 0 and x+1 < band.size[0] and y > 0 and y+1 < band.size[1]:
                    if (int(pixels[x-1,y] == 255) + int(pixels[x+1,y] == 255) + \
                            int(pixels[x,y-1] == 255) + int(pixels[x,y+1] == 255) >= 3) \
                            or pixels[x-1,y] == pixels[x+1,y] == 255\
                            or pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)
                    if pixels[x-1,y] == pixels[x+1,y] == 255 or\
                            pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[x, y] == 0 and x > 1 and x+2 < band.size[0] and y > 1 and y+2 < band.size[1]:
                    if (pixels[x-1,y] == pixels[x+2,y] == 255 and pixels[x+1,y] == 0) or\
                            (pixels[x,y-1] == pixels[x,y+2] == 255 and pixels[x,y+1] == 0):
                        band.putpixel(pixel, 255)
                if pixels[x, y] == 0 and x > 0 and x+1 < band.size[0] and y > 0 and y+1 < band.size[1]:
                    if pixels[x-1,y] == pixels[x+1,y] == 255 or\
                            pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)

        self.DFS()

        # Split the image
        blocks = list(blocks)
        boundary = [[150, 40, 0, 0] for k in range(4)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if not (x, y) in index:
                    continue
                idx = index[x, y]
                for k in range(4):
                    if idx == blocks[k]:
                        boundary[k][0] = min(boundary[k][0], x)
                        boundary[k][1] = min(boundary[k][1], y)
                        boundary[k][2] = max(boundary[k][2], x)
                        boundary[k][3] = max(boundary[k][3], y)
                        break
        part = {}
        characters = 0
        boundary = sorted(boundary, cmp=lambda x, y:cmp(x[0], y[0]))
        for k in range(4):
            part[k] = band.crop(tuple(boundary[k]))
            #part[k].show()
            #print boundary[k]
            #print part[k]
            if boundary[k][0] < boundary[k][2] and boundary[k][1] < boundary[k][3]:
                part[k].save(str(icode*4+k)+".png")
                characters += 1
        
        #band.show();band.save("codeR.png");sys.exit()
        if characters == 4:
            return True
        else:
            return False

class bg7:
    # Fill in some pixels by this surrounding pixels
    def mend_image(self, pixels, g, noise1, noise2, x, y):
        sur = [0, 0, 0, 0]
        for cur in range(4):
            sur[cur] = pixels[x + sur_d[cur][0], y + sur_d[cur][1]]
        if (sur[0] == sur[1] == 0 or sur[2] == sur[3] == 0)\
                and (pixels[x, y] < 255 or noise1[x, y] < 255 or noise2[x, y] < 255):
            g.putpixel((x, y), 0)
        if y+2 < g.size[1] and sur[2] == pixels[x, y+2] == 0 and sur[3] == 255\
                and (pixels[x, y] < 255 or noise1[x, y] < 255 or noise2[x, y] < 255):
            g.putpixel((x, y), 0)
             
    # Check up the pixel is or not in image 
    def mend_is_legal(self, pixel1, pixel2, color):
        #print pixel1, pixel2
        return pixel1[0] > 1 and pixel1[0] < pixel2[0] and pixel1[1] > 1 and pixel1[1] < pixel2[1] and color == 255

    # Use DFS to peel off isolated pixels
    def DFS(self):
        global band, blocks, index
        def dfs(pixel, block_id):
            if pixel[0] < 0 or pixel[0] >= band.size[0] \
                    or pixel[1] < 0 or pixel[1] >= band.size[1]:
                return
            if pixels[pixel] == 255 or pixel in vis:
                return
            vis.add(pixel)
            index[pixel] = block_id
            for k in range(8):
                dfs((pixel[0]+Delta[k][0], pixel[1]+Delta[k][1]), block_id)

        pixels = band.load()
        vis, q, index, block_id = set(), [], {}, 0
        q.append((0, 0))
        count = [[0, k] for k in range(100)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if not(pixel in vis) and pixels[pixel] == 0:
                    block_id += 1
                    dfs(pixel, block_id)
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if pixels[(x, y)] == 0:
                    count[index[(x, y)]][0] += 1
        count = sorted(count, cmp=lambda x,y:cmp(y[0],x[0]))
        blocks = set()
        for i in range(4):
            blocks.add(count[i][1])
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[pixel] == 0 and (not index[pixel] in blocks):
                    band.putpixel(pixel, 255)

    # Peel off this Authcode's background and noises, and change this image into black-and-white image
    def init_background(self, code, temp, icode=0):
        global band, blocks, index
        #code = code.filter(ImageFilter.DETAIL)
        bands = list(code.split())
        parameter = [1.3, 2, 1.3]
        for i in range(3):
            bands[i] = bands[i].point(lambda k: k*parameter[i])
        band = bands[0].load()
        for x in range(bands[0].size[0]):
            for y in range(bands[0].size[1]):
                if band[x, y] >= 230:
                    bands[0].putpixel((x, y), 200)
        peel_off_background()
        for i in range(3):
            #bands[i].save("codeL_"+str(i)+".png")
        #bands[1] = bands[1].point(lambda i: 255-i)
        band = bands[1]
        for i in range(3):
            bands[i] = bands[i].load()

        # Remove the noises by paramter
        pixels = band.load()
        count = [[0, i] for i in range(256)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                count[pixels[x, y] // 10][0] += 1
        count = sorted(count, cmp=lambda x,y:cmp(y[0],x[0]))
        """
        for i in range(26):
            if count[i][0] <= 10:
                break
            print "Color " + str(i) + " is", count[i][0], 10*count[i][1]
            """
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if 140 < pixels[x, y] < 255:
                    band.putpixel((x, y), 0)
                else:
                    band.putpixel((x, y), 255)
        
        # Mend the image, such as holes made by noises
        pixels = band.load()
        for X in range(band.size[0]):
            for Y in range(band.size[1]):
                x, y = band.size[0]-X-1, band.size[1]-Y-1
                key = pixels[x, y]
                if self.mend_is_legal((x+1, y+1), band.size, key):
                    self.mend_image(pixels, band, bands[0], bands[2], x, y)

        pixels = band.load()
        for X in range(band.size[0]):
            for Y in range(band.size[1]):
                x, y = band.size[0]-X-1, band.size[1]-Y-1
                key = pixels[x, y]
                if self.mend_is_legal((x+1, y+1), band.size, key):
                    self.mend_image(pixels, band, bands[0], bands[2], x, y)

        # Remove other noises by DFS, such as circle and isolate point
        blocks, index = set(), {}
        pixels = band.load()
        self.DFS()
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[x, y] == 0 and x > 0 and x+1 < band.size[0] and y > 0 and y+1 < band.size[1]:
                    if (int(pixels[x-1,y] == 255) + int(pixels[x+1,y] == 255) + \
                            int(pixels[x,y-1] == 255) + int(pixels[x,y+1] == 255) >= 3) \
                            or pixels[x-1,y] == pixels[x+1,y] == 255\
                            or pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)
                    if pixels[x-1,y] == pixels[x+1,y] == 255 or\
                            pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                pixel = (x, y)
                if pixels[x, y] == 0 and x > 1 and x+2 < band.size[0] and y > 1 and y+2 < band.size[1]:
                    if (pixels[x-1,y] == pixels[x+2,y] == 255 and pixels[x+1,y] == 0) or\
                            (pixels[x,y-1] == pixels[x,y+2] == 255 and pixels[x,y+1] == 0):
                        band.putpixel(pixel, 255)
                if pixels[x, y] == 0 and x > 0 and x+1 < band.size[0] and y > 0 and y+1 < band.size[1]:
                    if pixels[x-1,y] == pixels[x+1,y] == 255 or\
                            pixels[x,y-1] == pixels[x,y+1] == 255:
                        band.putpixel(pixel, 255)

        self.DFS()

        # Split the image
        blocks = list(blocks)
        boundary = [[150, 40, 0, 0] for k in range(4)]
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if not (x, y) in index:
                    continue
                idx = index[x, y]
                for k in range(4):
                    if idx == blocks[k]:
                        boundary[k][0] = min(boundary[k][0], x)
                        boundary[k][1] = min(boundary[k][1], y)
                        boundary[k][2] = max(boundary[k][2], x)
                        boundary[k][3] = max(boundary[k][3], y)
                        break
        for x in range(band.size[0]):
            for y in range(band.size[1]):
                if 70 < bands[0][x, y] < 140:
                    band.putpixel((x, y), 255)
        part = {}
        characters = 0
        boundary = sorted(boundary, cmp=lambda x, y:cmp(x[0], y[0]))
        for k in range(4):
            part[k] = band.crop(tuple(boundary[k]))
            #part[k].show()
            #print boundary[k]
            #print part[k]
            if boundary[k][0] < boundary[k][2] and boundary[k][1] < boundary[k][3]:
                part[k].save(str(icode*4+k)+".png")
                characters += 1
        
        #band.show();band.save("codeR.png");sys.exit()
        if characters == 4:
            return True
        else:
            return False

class Recognize:
    # Load 72 charecters(Arial Black) consists of normal type and italic type
    def __init__(self):
        global chars
        for k in range(72):
            chars[k] = Image.open("charecter/char"+str(k)+".png")

    # Calculate the similer degree between char1 and char2, such as row, column and all image
    def check_up_pattern(self, char1, char2):
        size = char1.size
        char1, char2 = char1.load(),  char2.load()

        result, count = 1.0, 0.0
        for x in range(size[0]):
            Cnt = 0
            for y in range(size[1]):
                if char1[x, y] == char2[x, y]:
                    Cnt += 1
            count += 1.0 * Cnt / size[1]
        result *= 1.0 * count / size[0]

        count = 0.0
        for y in range(size[1]):
            Cnt = 0
            for x in range(size[0]):
                if char1[x, y] == char2[x, y]:
                    Cnt += 1
            count += 1.0 * Cnt / size[0]
        result *= 1.0 * count / size[1]

        count = 0
        for x in range(size[0]):
            for y in range(size[1]):
                if char1[x, y] == char2[x, y]:
                    count += 1
        result += 1.0 * count / (size[0] * size[1])
        return result

    def recognize(self, url):
        try:
            im = Image.open(url)

            char = {}
            I = 0
            for i in range(72):
                ratio1 = 1.0 * chars[i].size[0] / chars[i].size[1]
                ratio2 = 1.0 * im.size[0] / im.size[1]
                if abs(ratio1 - ratio2) < 0.15:
                    char[I] = [0, alphabet[i]]
                    char[I][0] = chars[i].resize(im.size)
                    I += 1
            alpha = []
            for j in range(I):
                alpha.append([self.check_up_pattern(im, char[j][0]), char[j][1]])
            alpha = sorted(alpha, cmp=lambda x,y:cmp(y[0], x[0]))
            #print k, [alpha[j][1] for j in range(min(len(alpha), 15))]
            return alpha[0][1] if len(alpha)>0 else "#"

        except IOError:
            return "@"

#def main():
data = open('2013.csv', 'r')
writ = open('result.txt', 'w')
erro = open('error.txt', 'w')

# initilize recogntion
init_background()
sys.setrecursionlimit(32768)
R = Recognize()

# initilize query
B1 = "查询".decode('utf-8').encode('gbk')
scores_name = ["文化课总分", "语文", "数学", "外语", "综合"]
count = 0
Error = False

for line in data:
    if Error:
        erro.write(line)
        continue
    count += 1
    State = True # Deal with input error 
    line = line[:-1]
    blob = line.split('\t')
    num = blob[0]
    name = blob[1]
    scores = ["" for k in range(5)]
    while State:
        try:
            # Use Cookie to fake the server
            cookie_support= urllib2.HTTPCookieProcessor(cookielib.CookieJar())
            opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
            urllib2.install_opener(opener)
            headers = {
                       'Host':'51a.gov.cn',
                       'Origin':'http://51a.gov.cn',
                       'Referer':'http://51a.gov.cn/gk_lq.asp?action=do',
                       'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.63 Safari/537.31'
                    }
            # Get AuthCode
            outfile = open('code.jpg', 'w')
            outfile.write(opener.open(urllib2.Request(
                url = 'http://51a.gov.cn/getCode.asp',
                data = '',
                headers = headers
            )).read())
            outfile.close()
            # Recognize Code
            band = code = Image.open("code.jpg")
            bg_type = get_background()
            temp = background[bg_type]
            if bg_type == 0:
                authcode = bg1()
            elif bg_type == 1:
                authcode = bg2()
            elif bg_type == 2:
                authcode = bg3()
            elif bg_type == 3:
                authcode = bg4()
            elif bg_type == 4:
                authcode = bg5()
            elif bg_type == 5:
                authcode = bg6()
            elif bg_type == 6:
                authcode = bg7()
            authcode.init_background(code, temp)
            Code = ""
            for k in range(4):
                Code += R.recognize(str(k) + ".png")
            #code = raw_input('The '+str(count)+' th dataset. Please enter the authcode:')
            print 'The ' + str(count) + "th dataset."
            # Send query request
            content = opener.open(urllib2.Request(
                url = 'http://51a.gov.cn/gk_result.asp?action=do', 
                data = urllib.urlencode({
                    'id': num, 
                    'un': name.decode('utf-8').encode('gbk'),
                    'code': Code,    
                    'B1': B1 
                }), 
                headers = headers
            )).read()
            # Find the content what we needed
            content = content.decode('gbk').encode('utf-8')

            try:
                """
                test_re = open("test.htm", "w")
                test_re.write(content)
                print content
                """
                nofound = re.search("没有您的成绩资料", content)
                get_authcode = re.search("验证码输入错误", content)
                for k in range(5):
                    scores[k] = re.search("<b>" + scores_name[k] +"：</b><font color=red>([^<]+)</font></td>", content).group(1).strip()
                    #print scores[k]

            except AttributeError:
                for k in range(5):
                    scores[k] = ""
                if nofound:
                    print 'ERROR!'

            if len(scores[0]) > 0 and not nofound and not get_authcode:
                State = False
                result = line
                for k in range(5):
                    result += '\t' + scores[k]
                writ.write(result + '\n')
            elif nofound:
                State = False
                writ.write(line + '\n')

        except urllib2.URLError:
            erro.write(line + '\n')

        except EOFError:
            State = False
            Error = True
            break

#if __name__ == '__main__':
#    main()
