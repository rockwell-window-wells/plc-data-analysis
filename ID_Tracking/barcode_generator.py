from barcode import Code128
from barcode.writer import ImageWriter

prefix = 23
id = 672
number = str(prefix) + str(id)

code = Code128(number, writer=ImageWriter())

imgname = "images/testbarcode"
code.save(imgname)
