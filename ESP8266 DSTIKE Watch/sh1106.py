_A=None
from micropython import const
import utime as time,framebuf
_SET_CONTRAST=const(129)
_SET_NORM_INV=const(166)
_SET_DISP=const(174)
_SET_SCAN_DIR=const(192)
_SET_SEG_REMAP=const(160)
_LOW_COLUMN_ADDRESS=const(0)
_HIGH_COLUMN_ADDRESS=const(16)
_SET_PAGE_ADDRESS=const(176)
class SH1106(framebuf.FrameBuffer):
	def __init__(A,width,height,external_vcc,rotate=0):
		B=rotate;A.width=width;A.height=height;A.external_vcc=external_vcc;A.flip_en=B==180 or B==270;A.rotate90=B==90 or B==270;A.pages=A.height//8;A.bufsize=A.pages*A.width;A.renderbuf=bytearray(A.bufsize);A.pages_to_update=0;A.delay=0
		if A.rotate90:A.displaybuf=bytearray(A.bufsize);super().__init__(A.renderbuf,A.height,A.width,framebuf.MONO_HMSB)
		else:A.displaybuf=A.renderbuf;super().__init__(A.renderbuf,A.width,A.height,framebuf.MONO_VLSB)
		A.rotate=A.flip;A.init_display()
	def write_cmd(A,*B,**C):raise NotImplementedError
	def write_data(A,*B,**C):raise NotImplementedError
	def init_display(A):A.reset();A.fill(0);A.show();A.poweron();A.flip(A.flip_en)
	def poweroff(A):A.write_cmd(_SET_DISP|0)
	def poweron(A):
		A.write_cmd(_SET_DISP|1)
		if A.delay:time.sleep_ms(A.delay)
	def flip(A,flag=_A,update=True):
		B=flag
		if B is _A:B=not A.flip_en
		C=B^A.rotate90;D=B;A.write_cmd(_SET_SEG_REMAP|(1 if C else 0));A.write_cmd(_SET_SCAN_DIR|(8 if D else 0));A.flip_en=B
		if update:A.show(True)
	def sleep(A,value):A.write_cmd(_SET_DISP|(not value))
	def contrast(A,contrast):A.write_cmd(_SET_CONTRAST);A.write_cmd(contrast)
	def invert(A,invert):A.write_cmd(_SET_NORM_INV|invert&1)
	def show(A,full_update=False):
		B,E,F,H=A.width,A.pages,A.displaybuf,A.renderbuf
		if A.rotate90:
			for D in range(A.bufsize):F[B*(D%E)+D//E]=H[D]
		if full_update:G=(1<<A.pages)-1
		else:G=A.pages_to_update
		for C in range(A.pages):
			if G&1<<C:A.write_cmd(_SET_PAGE_ADDRESS|C);A.write_cmd(_LOW_COLUMN_ADDRESS|2);A.write_cmd(_HIGH_COLUMN_ADDRESS|0);A.write_data(F[B*C:B*C+B])
		A.pages_to_update=0
	def pixel(B,x,y,color=_A):
		A=color
		if A is _A:return super().pixel(x,y)
		else:super().pixel(x,y,A);C=y//8;B.pages_to_update|=1<<C
	def text(A,text,x,y,color=1):super().text(text,x,y,color);A.register_updates(y,y+7)
	def line(A,x0,y0,x1,y1,color=1):super().line(x0,y0,x1,y1,color);A.register_updates(y0,y1)
	def hline(A,x,y,w,color=1):super().hline(x,y,w,color);A.register_updates(y)
	def vline(A,x,y,h,color=1):super().vline(x,y,h,color);A.register_updates(y,y+h-1)
	def fill(A,color):super().fill(color);A.pages_to_update=(1<<A.pages)-1
	def blit(A,fbuf,x,y,key=-1,palette=_A):super().blit(fbuf,x,y,key,palette);A.register_updates(y,y+A.height)
	def scroll(A,x,y):super().scroll(x,y);A.pages_to_update=(1<<A.pages)-1
	def fill_rect(A,x,y,w,h,color=1):super().fill_rect(x,y,w,h,color);A.register_updates(y,y+h-1)
	def rect(A,x,y,w,h,color=1):super().rect(x,y,w,h,color);A.register_updates(y,y+h-1)
	def ellipse(A,x,y,xr,yr,color):super().ellipse(x,y,xr,yr,color);A.register_updates(y-yr,y+yr-1)
	def register_updates(C,y0,y1=_A):
		A=max(0,y0//8);B=max(0,y1//8)if y1 is not _A else A
		if A>B:A,B=B,A
		for D in range(A,B+1):C.pages_to_update|=1<<D
	def reset(B,res=_A):
		A=res
		if A is not _A:A(1);time.sleep_ms(1);A(0);time.sleep_ms(20);A(1);time.sleep_ms(20)
class SH1106_I2C(SH1106):
	def __init__(A,width,height,i2c,res=_A,addr=60,rotate=0,external_vcc=False,delay=0):
		B=res;A.i2c=i2c;A.addr=addr;A.res=B;A.temp=bytearray(2);A.delay=delay
		if B is not _A:B.init(B.OUT,value=1)
		super().__init__(width,height,external_vcc,rotate)
	def write_cmd(A,cmd):A.temp[0]=128;A.temp[1]=cmd;A.i2c.writeto(A.addr,A.temp)
	def write_data(A,buf):A.i2c.writeto(A.addr,b'@'+buf)
	def reset(A,res=_A):super().reset(A.res)

