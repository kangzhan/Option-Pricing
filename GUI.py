from Option import *
import tkinter as tk
import tkinter.messagebox

# 期权类型 derivative_type
w.start()
use_his_vol = True
def set_from_wind_data():
    price.set(str(w.wsd(code.get(), "close", "ED-5TD", current_date.get(), "Fill=Previous;PriceAdj=F").Data[0][-1]))


def pricing():
    try:
        o_type = option_type.get(option_type.curselection()[0])
    except IndexError:
        tk.messagebox.showerror('Error', '未选定衍生品种类')
        return None
    if o_type == 'Europe Call':
        try:
            option = EuroCall(code.get(), float(price.get()), int(expiration_time.get()),
                              float(risk_free_interest.get()), float(his_vol1.get()), float(strike_p1.get()))
        except ValueError:
            tk.messagebox.showerror('Error', '输入数据类型有误')
            return None
        if use_his_vol:
            option.set_his_vol(current_date.get())
        option.pricing(float(er.get()), message_box=tk.messagebox)
    elif o_type == 'Europe Put':
        try:
            option = EuroPut(code.get(), float(price.get()), int(expiration_time.get()),
                             float(risk_free_interest.get()), float(strike_p1.get()), float(his_vol1.get()))
        except ValueError:
            tk.messagebox.showerror('Error', '输入数据类型有误')
            return None
        if use_his_vol:
            option.set_his_vol(current_date.get())
        option.pricing(equity_ratio=float(er.get()), message_box=tk.messagebox)

root = tk.Tk()
root.title = 'Option Pricing'
# 期权种类选择

up_part = tk.Frame(root)
left_part = tk.Frame(up_part)

parameter_frame = tk.LabelFrame(left_part, text="Option Parameters")
section = parameter_frame
strike_p1 = tk.StringVar()
strike_p2 = tk.StringVar()
strike_p3 = tk.StringVar()
barrier1 = tk.StringVar()
barrier1_type = tk.StringVar()
barrier2 = tk.StringVar()
barrier2_type = tk.StringVar()
expiration_time = tk.StringVar()
risk_free_interest = tk.StringVar()
margin_rate = tk.StringVar()
divident= tk.StringVar()
temp_frame = tk.LabelFrame(section, text='strike price1')
tk.Entry(temp_frame, textvariable=strike_p1).pack()
temp_frame.pack(fill="both", side=tk.TOP)
temp_frame = tk.LabelFrame(section, text='strike price2')
tk.Entry(temp_frame, textvariable=strike_p2).pack()
temp_frame.pack(fill="both", side=tk.TOP)
temp_frame = tk.LabelFrame(section, text='strike price3')
tk.Entry(temp_frame, textvariable=strike_p3).pack()
temp_frame.pack(fill="both", side=tk.TOP)
temp_frame = tk.LabelFrame(section, text="barrier1 price")
tk.Entry(temp_frame, textvariable=barrier1).pack()
temp_frame.pack(fill="both", side=tk.TOP)
temp_frame = tk.LabelFrame(section, text="barrier1 type")
tk.Entry(temp_frame, textvariable=barrier1_type).pack()
temp_frame.pack(fill="both", side=tk.TOP)
temp_frame = tk.LabelFrame(section, text="barrier2 price")
tk.Entry(temp_frame, textvariable=barrier2).pack()
temp_frame.pack(fill="both", side=tk.TOP)
temp_frame = tk.LabelFrame(section, text="barrier2 type")
tk.Entry(temp_frame, textvariable=barrier2_type).pack()
temp_frame.pack(fill="both", side=tk.TOP)
temp_frame = tk.LabelFrame(section, text="expiration")
tk.Entry(temp_frame, textvariable=expiration_time).pack()
temp_frame.pack(fill="both", side=tk.TOP)
temp_frame = tk.LabelFrame(section, text="risk free rate")
tk.Entry(temp_frame, textvariable=risk_free_interest).pack()
temp_frame.pack(fill="both", side=tk.TOP)
temp_frame = tk.LabelFrame(section, text="margin rate")
tk.Entry(temp_frame, textvariable=margin_rate).pack()
temp_frame.pack(fill="both", side=tk.TOP)
temp_frame = tk.LabelFrame(section, text="divident")
tk.Entry(temp_frame, textvariable=divident).pack()
temp_frame.pack(fill="both", side=tk.TOP)
parameter_frame.pack(fill="both", side=tk.TOP)
left_part.pack(fill="both", side=tk.LEFT)
# left part end

right_part = tk.Frame(up_part)
option_frame = tk.LabelFrame(right_part, text="Option Type")
option_frame.pack(fill="none", side=tk.TOP)
section = option_frame
derivative_type = tk.StringVar()
option_type = tk.Listbox(section, listvariable=derivative_type)
for item in ['Europe Call', 'Europe Put']:
    option_type.insert(tk.END,item)
sl = tk.Scrollbar(section)
sl.pack(side = tk.RIGHT,fill = tk.Y)
option_type['yscrollcommand'] = sl.set
option_type.pack(fill="both", side = tk.LEFT)
sl['command'] = option_type.yview
pricing_frame = tk.LabelFrame(right_part, text='Underlying Parameters')
price = tk.StringVar()
code = tk.StringVar()
his_vol1 = tk.StringVar()
er = tk.StringVar()
section = pricing_frame
temp_frame = tk.LabelFrame(section, text='underlying code')
tk.Entry(temp_frame, textvariable=code).pack()
temp_frame.pack(fill="both", side=tk.TOP)
temp_frame = tk.LabelFrame(section, text='underlying price')
tk.Entry(temp_frame, textvariable=price).pack()
temp_frame.pack(fill="both", side=tk.TOP)
temp_frame = tk.LabelFrame(section, text='historical volatility')
tk.Entry(temp_frame, textvariable=his_vol1).pack()
temp_frame.pack(fill="both", side=tk.TOP)
temp_frame = tk.LabelFrame(section, text='equity ratio')
tk.Entry(temp_frame, textvariable=er).pack()
temp_frame.pack(fill="both", side=tk.TOP)
pricing_frame.pack(fill="both", side=tk.TOP)
current_date = tk.StringVar()
temp_frame = tk.LabelFrame(section, text='current date')
tk.Entry(temp_frame, textvariable=current_date).pack()
temp_frame.pack(fill="both", side=tk.TOP)

right_part.pack(fill="both", side=tk.RIGHT)
up_part.pack(fill="both", side=tk.TOP)
button_part = tk.Frame(root)
set_from_wind = tk.Button(button_part, text='Set From Wind', command=set_from_wind_data)
set_from_wind.pack(fill="both", side=tk.LEFT)
price_button = tk.Button(button_part, text='Get Pricing', command=pricing)
price_button.pack(fill="both", side=tk.LEFT)
button_part.pack(fill="both", side=tk.BOTTOM)
tk.mainloop()