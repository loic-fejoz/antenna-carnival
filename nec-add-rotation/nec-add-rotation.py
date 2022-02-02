
def protect_coord(c):
    if "+" in c or "(" in c or "-" in c:
        return "("+c+")"
    else:
        return c

def simplify(c):
    if c.startswith("0+"):
        return c[2:]
    else:
        return c

mat_rot = [
["cos(y_angle)*cos(z_angle)", "-cos(y_angle)*sin(z_angle)", "sin(y_angle)"],
["(cos(z_angle)*sin(x_angle)*sin(y_angle) + cos(x_angle)*sin(z_angle))", "(-sin(x_angle)*sin(y_angle)*sin(z_angle) + cos(x_angle)*cos(z_angle))", "-cos(y_angle)*sin(x_angle)"],
["(-cos(x_angle)*cos(z_angle)*sin(y_angle) + sin(x_angle)*sin(z_angle))", "(cos(x_angle)*sin(y_angle)*sin(z_angle) + cos(z_angle)*sin(x_angle))", "cos(x_angle)*cos(y_angle)"]
]


def mul(a, b):
    if a == "0":
        return "0"
    if b == "0":
        return "0"
    return a + "*" + b

def add(a, b):
    if a == "0":
        return b
    if b == "0":
        return a
    return "(" + a + "+" + b + ")"

def transform(p):
    p = list(map(protect_coord, p))
    p_t = [
        add(add(mul(p[0],mat_rot[0][0]),mul(p[1], mat_rot[0][1])),mul(p[2],mat_rot[0][2])),
        add(add(mul(p[0],mat_rot[1][0]),mul(p[1], mat_rot[1][1])),mul(p[2],mat_rot[1][2])),
        add(add(mul(p[0],mat_rot[2][0]),mul(p[2], mat_rot[2][1])),mul(p[2],mat_rot[2][2])),
    ]
    p_t = [p_t[0], p_t[1], p_t[2] + "+h"]
    return list(map(simplify, p_t))

def rotate_translate(input, output):
    in_symbol = True
    for line in input:
        if line.startswith("GW"):
            if in_symbol:
                in_symbol = False
                # This is end of symbol
                output.write("SY h=1.5\n")
                output.write("SY x_angle=0\n")
                output.write("SY y_angle=0\n")
                output.write("SY z_angle=0\n")
            gw_data = line.split("\t")
            p1 = gw_data[3:6]
            p2 = gw_data[6:9]
            print(p1, p2)
            p1_trans = transform(p1)
            p2_trans = transform(p2)
            gw_data[3:6] = p1_trans
            gw_data[6:9] = p2_trans
            output.write("\t".join(gw_data))
        else:
            output.write(line)

def handle(filename):
    with open(filename, "r") as input:
        with open(filename[:-4]+"-rotated.nec", "w") as output:
            rotate_translate(input, output)

handle("my-J145_440-v2.nec")