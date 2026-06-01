# opencv-python numpy pillow pdf2image
import cv2, os, sys
import numpy as np
import tkinter as tk
from tkinter import filedialog as fd
from PIL import Image
from pdf2image import convert_from_path as cvt
Image.MAX_IMAGE_PIXELS = None

# 自動偵測是否為 PyInstaller 打包環境，並動態導向內建的 poppler 路徑
if getattr(sys, 'frozen', False):
    POP = os.path.join(sys._MEIPASS, "poppler", "bin")
else:
    # 這是開發階段（未打包）時你在 Windows 上的實際路徑
    POP = r"C:\poppler\bin"

def norm(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    high = np.percentile(gray, 90) or 1.0
    gain = 255.0 / high
    res = np.clip(img.astype(np.float32) * gain, 0, 255).astype(np.uint8)
    _, mask = cv2.threshold(gray * gain, 240, 255, cv2.THRESH_BINARY)
    res[mask == 255] = 255
    return res

def proc(src, dst):
    ext = os.path.splitext(src)[1].lower()
    if ext == '.pdf':
        pgs = cvt(src, dpi=150, poppler_path=POP)
        imgs = []
        for pg in pgs:
            bgr = cv2.cvtColor(np.array(pg), cv2.COLOR_RGB2BGR)
            out = norm(bgr)
            rgb = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
            imgs.append(Image.fromarray(rgb, 'RGB'))
        imgs[0].save(dst, save_all=True, append_images=imgs[1:])
    elif ext in ['.jpg', '.jpeg', '.png', '.bmp']:
        bgr = cv2.imread(src)
        if bgr is not None:
            cv2.imwrite(dst, norm(bgr))

if __name__ == "__main__":
    # 使用 try-except 包裹主程式，避免打包後出錯直接閃退
    try:
        root = tk.Tk()
        root.withdraw()

        if len(sys.argv) >= 2:
            inp = sys.argv[1]
        else:
            inp = fd.askopenfilename(title="請選擇來源檔案")
            if not inp:
                sys.exit(0)

        if len(sys.argv) >= 3:
            out = sys.argv[2]
        else:
            base, ext = os.path.splitext(inp)
            out = fd.asksaveasfilename(
                title="請選擇儲存位置",
                initialfile=f"{os.path.basename(base)}_fixed{ext}",
                filetypes=[("預設格式", f"*{ext}"), ("所有檔案", "*.*")]
            )
            if not out:
                sys.exit(0)
            
        proc(inp, out)
        
        # 關鍵：強制銷毀 Tk 主視窗，防止背景進程殘留
        root.quit()
        root.destroy()
        
    except Exception as err:
        # 如果出錯，彈出視窗提示錯誤訊息，方便排錯
        from tkinter import messagebox
        messagebox.showerror("錯誤", str(err))
