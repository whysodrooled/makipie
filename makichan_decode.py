# every information from https://mooncore.eu/bunny/txt/makichan.htm

# TODO: do something about additional 4 pixels in the right side of zarth.mag
# TODO: kinda lacking blue in yjk pictures

from PIL import Image
import numpy as np
import math

def Unsigned_To_Signed_6bit(val):
    if val & (1 << 5) != 0:
        val = (val & 0b011111) - 32
    return val

def Decode_MAKI01(data):
    #f_format = data[:8].decode("ANSI")
    #if f_format.find("MAKI01") == -1:
    #    return "Not a MAKI01 File"

    xor_offs = 2
    if data[6:8].decode("ANSI") == "B ": xor_offs = 4

    description = data[12:32]
    description_end = description.find(b'\x1A')
    if description_end != -1:
        description = description[:description_end]
    description = description.decode(encoding="Shift-JIS", errors="replace")

    flagB_start = int.from_bytes(data[32:34], byteorder="big") + 1096
    #pixelA_size = int.from_bytes(data[34:36], byteorder="big")
    #pixelB_size = int.from_bytes(data[36:38], byteorder="big")
    ext_Flag = int.from_bytes(data[38:40], byteorder="big")
    width = int.from_bytes(data[44:46], byteorder="big")
    height = int.from_bytes(data[46:48], byteorder="big")
    palette = [(data[i+1], data[i], data[i+2]) for i in range(48, 97, 3)]

    # misato.mki didn't work properly with this validation
    #if len(data) != flagB_start + pixelA_size + pixelB_size:
        #return "Not a valid MAKI01 File"

    result_img = Image.new("RGB", (width, height))
    result_pixels = result_img.load()

    exist_pixel = np.zeros((height, width // 2), dtype=int)
    counter = 1096
    curx = 0
    cury = 0
    for i in range(96, 1097):
        for j in range(0, 8):
            if data[i] & (0b10000000 >> j):
                for k in range(0, 16):
                    if (data[counter + (k // 8)] & (0b10000000 >> (k % 8))) != 0:
                        exist_pixel[cury + (k // 4)][curx + (k % 4)] = 1

                counter += 2
            
            curx += 4

        if curx >= width // 2:
            curx = 0
            cury += 4

        if counter >= flagB_start or cury >= height: break

    for i, array in enumerate(exist_pixel):
        for j, palinfo in enumerate(array):
            if palinfo:
                exist_pixel[i][j] = data[counter]
                counter += 1
            if i >= xor_offs:
                exist_pixel[i][j] ^= exist_pixel[i - xor_offs][j]
            
            result_pixels[j * 2, i] = palette[exist_pixel[i][j] >> 4]
            result_pixels[j * 2 + 1, i] = palette[exist_pixel[i][j] & 0b1111]
    
    if (ext_Flag & 0b1) != 0:
        result_img = result_img.resize((width, height * 2), Image.NEAREST)
    elif (ext_Flag & 0b10) != 0:
        # legacy 8 color flag
        pass

    return (result_img, description)

def Decode_MAKI02(data):
    #f_format = data[:8].decode("ANSI")
    #if f_format.find("MAKI02  ") != 0:
    #    return "Not a MAKI02 File"

    description = b''
    h_start = 12
    while True:
        if data[h_start] == 0x1A:
            h_start += 1
            break
        description += bytes((data[h_start],)) # idk why i have to put ',' in order to get it work
        h_start += 1
    description = description.decode(encoding="Shift-JIS", errors="replace")

    h_model = int(data[h_start+1])
    h_model_flag = int(data[h_start+2])
    h_screen_mode = int(data[h_start+3])

    h_color256 = bool(h_screen_mode >> 7)
    h_padleft = (int.from_bytes(data[h_start+4:h_start+6], byteorder="little") // (2 - int(h_color256))) & 0xFFFC
    h_padright = (int.from_bytes(data[h_start+8:h_start+10], byteorder="little") // (2 - int(h_color256)) + 4) & 0xFFFC
    h_bytewidth = h_padright - h_padleft
    h_width = h_bytewidth * (2 - int(h_color256))
    h_height = int.from_bytes(data[h_start+10:h_start+12], byteorder="little") - int.from_bytes(data[h_start+6:h_start+8], byteorder="little") + 1
    h_height_double = False

    h_flagA_loc = h_start + int.from_bytes(data[h_start+12:h_start+16], byteorder="little")
    h_flagB_loc = h_start + int.from_bytes(data[h_start+16:h_start+20], byteorder="little")
    #h_flagB_size = int.from_bytes(data[h_start+20:h_start+24], byteorder="little")
    h_coloridx_loc = h_start + int.from_bytes(data[h_start+24:h_start+28], byteorder="little")
    h_coloridx_size = int.from_bytes(data[h_start+28:h_start+32], byteorder="little")

    if len(data) != h_coloridx_loc + h_coloridx_size:
        return "Not a valid MAKI02 File"

    palette_bits = 4
    yjk_decode = False
    squash = False
    if h_model != 0x3:
        if (h_screen_mode <= 128) and (h_screen_mode % 2 == 1):
            h_height_double = True
        elif h_screen_mode == 129 or h_screen_mode == 132 or h_screen_mode == 133:
            h_height = 212
        
        if h_model == 0x68:
            palette_bits = 5
        elif h_model == 0x99 and (h_model != 0x88 and ((h_flagA_loc-(h_start+31)) // 3 == 256)):
            palette_bits = 8
    else:
        # handling msx perks. i dont quite get this one
        if h_model_flag <= 0x54:
            if h_model_flag >= 0x20 and h_model_flag <= 0x44:
                yjk_decode = True
                #if h_model_flag & 0x4 != 0 and h_screen_mode < 128:
                if h_screen_mode < 0x10:
                    h_width = 256
            if h_model_flag > 0 and h_model_flag & 0x4 == 0:
                squash = True
            elif h_model_flag == 4 and h_screen_mode == 1:
                h_height_double = True
        elif (h_model_flag >= 0x60 and h_model_flag < 0x70) or ((h_flagA_loc-(h_start+31)) // 3 == 4):
            h_width *= 2
            if h_model_flag == 0x64: h_height_double = True
        
        #h_height = 212
        if data[32:43] == bytearray("Deca loader", "ANSI"):
            if h_model_flag == 0x14:
                palette_bits = 8
            else:
                palette_bits = 4
        else:
            palette_bits = 3

    palette = []
    if palette_bits == 8:
        for i in range(h_start+32, h_flagA_loc):
            if (i - (h_start+32)) % 3 == 2:
                palette.append((data[i-1], data[i-2], data[i]))
    else:
        for i in range(h_start+32, h_flagA_loc):
            data[i] &= ((2 ** palette_bits - 1) << 8 - palette_bits)
            for j in range(palette_bits, 8, palette_bits):
                data[i] |= (data[i] >> j)

            if (i - (h_start+32)) % 3 == 2:
                palette.append((data[i-1], data[i-2], data[i]))

    result_img = Image.new("RGB", (h_width, h_height))
    result_pixels = result_img.load()

    buf_output = np.zeros(h_height * h_bytewidth, dtype=int)
    buf_action = np.zeros(h_bytewidth // 4, dtype=int)
    counter_action = 0
    counter_coloridx = h_coloridx_loc
    counter_output = 0
    counter_flagB = h_flagB_loc
    curx = 0
    cury = 0
    nibble = 0
    bTerminate = False

    for i in range(h_flagA_loc, h_flagB_loc):
        for j in range(0, 8):
            if data[i] & (0b10000000 >> j) != 0:
                buf_action[counter_action] = data[counter_flagB] ^ buf_action[counter_action]
                counter_flagB += 1

            for k in range(0, 2):
                if k == 1:
                    nibble = buf_action[counter_action] & 0b1111
                else:
                    nibble = buf_action[counter_action] >> 4

                if nibble == 0:
                    if counter_coloridx >= len(data):
                        break
                    buf_output[counter_output] = data[counter_coloridx]
                    buf_output[counter_output+1] = data[counter_coloridx+1]
                    counter_coloridx += 2
                else:
                    # i miss the switch statement mommy
                    if nibble == 1:
                        curx = 1
                        cury = 0
                    elif nibble == 2:
                        curx = 2
                        cury = 0
                    elif nibble == 3:
                        curx = 4
                        cury = 0
                    elif nibble == 4:
                        curx = 0
                        cury = 1
                    elif nibble == 5:
                        curx = 1
                        cury = 1
                    elif nibble == 6:
                        curx = 0
                        cury = 2
                    elif nibble == 7:
                        curx = 1
                        cury = 2
                    elif nibble == 8:
                        curx = 2
                        cury = 2
                    elif nibble == 9:
                        curx = 0
                        cury = 4
                    elif nibble == 10:
                        curx = 1
                        cury = 4
                    elif nibble == 11:
                        curx = 2
                        cury = 4
                    elif nibble == 12:
                        curx = 0
                        cury = 8
                    elif nibble == 13:
                        curx = 1
                        cury = 8
                    elif nibble == 14:
                        curx = 2
                        cury = 8
                    elif nibble == 15:
                        curx = 0
                        cury = 16

                    offs = curx * 2 + h_bytewidth * cury
                    buf_output[counter_output] = buf_output[counter_output-offs]
                    buf_output[counter_output+1] = buf_output[counter_output-offs+1]

                counter_output += 2
                if counter_output >= len(buf_output):
                    bTerminate = True
                    break

            if bTerminate: break

            counter_action += 1
            if counter_action >= h_bytewidth // 4: counter_action = 0

        if bTerminate: break

    curx = 0
    cury = 0

    if yjk_decode:
        for i in range(0, len(buf_output), 4):
            val_k = Unsigned_To_Signed_6bit((buf_output[i] & 0b111) + (buf_output[i+1] & 0b111) * 8)
            val_j = Unsigned_To_Signed_6bit((buf_output[i+2] & 0b111) + (buf_output[i+3] & 0b111) * 8)
            val_y = [None] * 4
            val_y[0] = buf_output[i] >> 3
            val_y[1] = buf_output[i+1] >> 3
            val_y[2] = buf_output[i+2] >> 3
            val_y[3] = buf_output[i+3] >> 3

            for y in val_y:
                if (h_model_flag == 0x24 or h_model_flag == 0x34) and y % 2 == 1:
                    result_pixels[curx, cury] = palette[y // 2]
                else:
                    result_pixels[curx, cury] = ((y + val_j) * 255 // 31, (y + val_k) * 255 // 31, math.ceil(5 * y / 4 - j / 2 - k / 4) * 255 // 31)
                curx += 1
    
            if curx >= h_width:
                curx = 0
                cury += 1
    elif h_color256:
        for i in range(0, len(buf_output), 2):
            result_pixels[curx, cury] = palette[buf_output[i]]
            result_pixels[curx+1, cury] = palette[buf_output[i+1]]
            curx += 2
            if curx >= h_width:
                curx = 0
                cury += 1
    elif (h_model_flag >= 0x60 and h_model_flag < 0x70): # this 2-bit palette thing was not shown in the website
        for i in range(0, len(buf_output), 2):
            result_pixels[curx, cury] = palette[buf_output[i] >> 6]
            result_pixels[curx+1, cury] = palette[(buf_output[i] & 0b110000) >> 4]
            result_pixels[curx+2, cury] = palette[(buf_output[i] & 0b1100) >> 2]
            result_pixels[curx+3, cury] = palette[buf_output[i] & 0b11]
            result_pixels[curx+4, cury] = palette[buf_output[i+1] >> 6]
            result_pixels[curx+5, cury] = palette[(buf_output[i+1] & 0b110000) >> 4]
            result_pixels[curx+6, cury] = palette[(buf_output[i+1] & 0b1100) >> 2]
            result_pixels[curx+7, cury] = palette[buf_output[i+1] & 0b11]
            curx += 8
            if curx >= h_width:
                curx = 0
                cury += 1
    else:
        for i in range(0, len(buf_output), 2):
            result_pixels[curx, cury] = palette[buf_output[i] >> 4]
            result_pixels[curx+1, cury] = palette[buf_output[i] & 0b1111]
            result_pixels[curx+2, cury] = palette[buf_output[i+1] >> 4]
            result_pixels[curx+3, cury] = palette[buf_output[i+1] & 0b1111]
            curx += 4
            if curx >= h_width:
                curx = 0
                cury += 1
            #if cury >= h_height: break

    if not yjk_decode and not (h_model_flag >= 0x60 and h_model_flag < 0x70):
        result_img = result_img.crop((h_padleft * (2 - int(h_color256)), 0, h_padright * (2 - int(h_color256)), result_img.size[1]))
    if squash:
        result_img = result_img.resize((h_width * 2, h_height), Image.NEAREST)

    if h_height_double:
        result_img = result_img.resize((h_width, h_height * 2), Image.NEAREST)
    
    return (result_img, description)

def Decode_MAKI(data):
    f_format = data[:8].decode("ANSI")
    if f_format.find("MAKI02  ") == 0:
        return Decode_MAKI02(data)
    elif f_format.find("MAKI01") == 0:
        return Decode_MAKI01(data)
    else:
        return "Not a MAKI file"