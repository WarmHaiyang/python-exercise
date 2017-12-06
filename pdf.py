import os
from reportlab.pdfgen import canvas
def mapd():
    nop = 0
    mulu = 'manhua' + os.path.sep + '圣斗士-冥王神话CH1-7话'
    list_dir = os.listdir(mulu)
    c = canvas.Canvas('pdf_dir' + os.path.sep + str(len(list_dir)) +'.pdf', pagesize = [1000,1000])
    while nop < len(list_dir):
        for a in list_dir:
            c.drawImage(mulu + os.path.sep + '%s' % a,0,0)
            c.showPage()
        nop = nop + 1
    else:
        c.save()
# for i in range(X,Y): #XY为重复区间，本程序要求图片按数字顺序排列
if __name__ == '__main__':
    mapd()
#nof 是 number of file, nop 是number of page