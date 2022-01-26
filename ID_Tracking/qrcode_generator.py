import qrcode

prefix = 23
id = 672
number = str(prefix) + str(id)

img = qrcode.make(number)
print(type(img))

filename = "images/testQR.png"
img.save(filename)
