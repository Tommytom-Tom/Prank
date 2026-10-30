"""Crée un cartoon animé original : python3 animation.py (Pillow requis)."""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


SIZE = 480
SCALE = 2
FPS = 25
FRAMES = 240
OUT = Path(__file__).with_name("macarena.gif")
NAME_FILE = Path(__file__).with_name("prenom.txt")
FACE_FILE = Path(__file__).with_name("face.png")
INK = "#26324b"
SKIN = "#db9e76"
SHIRT = "#53caba"
SHORTS = "#7962cb"
SHORTS_RED = "#db9e76"


def smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def mix(a, b, weight):
    return tuple(x + (y - x) * weight for x, y in zip(a, b))


# Chaque pose définit coude et main ; les deux bras suivent les temps décalés.
POSES = [
    ((-48, -26, 13), (-48, 0, 16)),
    ((-38, -48, 30), (-37, -56, 88)),
    ((-38, -48, 30), (-37, -56, 88)),
    ((-48, -25, 30), (24, -77, 24)),
    ((-48, -25, 30), (24, -77, 24)),
    ((-62, -72, 0), (-22, -106, -8)),
    ((-62, -72, 0), (-22, -106, -8)),
    ((-62, -22, 8), (-35, 18, 19)),
    ((-62, -22, 8), (-35, 18, 19)),
]


def font(size):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        return ImageFont.truetype(path, size * SCALE)
    except OSError:
        return ImageFont.load_default()


def load_first_name(path=NAME_FILE):
    """Lire une seule ligne logique en conservant accents et prénoms composés."""
    return " ".join(path.read_text(encoding="utf-8-sig").split())


def draw_first_name(draw, first_name):
    """Garder le titre centré et réduire sa taille pour les prénoms longs."""
    size = 30
    title_font = font(size)
    while size > 1:
        left, _, right, _ = draw.textbbox((0, 0), first_name, font=title_font)
        if right - left <= (SIZE - 40) * SCALE:
            break
        size -= 1
        title_font = font(size)
    draw.text((240 * SCALE, 40 * SCALE), first_name, font=title_font,
              fill=INK, anchor="mm")


def load_optional_face(path=FACE_FILE):
    """Préparer une fois le portrait ; l'absence du fichier est autorisée."""
    try:
        with Image.open(path) as source:
            # Remplir toute la zone, quitte à déformer les proportions d'origine.
            face = ImageOps.exif_transpose(source).convert("RGBA").resize(
                (50 * SCALE, 60 * SCALE), resample=Image.Resampling.LANCZOS,
            )
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as error:
        raise ValueError(f"Impossible de lire le visage dans {path} : {error}") from error
    return face


def paste_face(image, face, center, head_yaw):
    """Simuler le lacet du portrait par compression horizontale."""
    width = max(1, round(face.width * max(0, math.cos(head_yaw))))
    portrait = face.resize((width, face.height), Image.Resampling.LANCZOS)
    x, y = center
    position = (round(x * SCALE - width / 2), round(y * SCALE - face.height / 2))
    image.paste(portrait, position, portrait)


def render(index, first_name="", face=None):
    t = index / FPS
    beat = math.sin(2 * math.pi * t / 0.64)
    yaw = 0.0
    if 5.12 <= t < 6.4:
        yaw = math.pi * smooth((t - 5.12) / 1.28)
    elif 6.4 <= t < 8.96:
        yaw = math.pi + 0.13 * math.sin(2 * math.pi * (t - 6.4) / 0.64)
    elif t >= 8.96:
        yaw = math.pi + math.pi * smooth((t - 8.96) / 0.64)
    # Regard par-dessus l'épaule, indépendant de la rotation du corps.
    look_back = smooth((t - 7.36) / 0.48) * (1 - smooth((t - 8.64) / 0.32))
    head_yaw = yaw + (0.25 - yaw) * look_back
    tongue = smooth((t - 7.84) / 0.16) * (1 - smooth((t - 8.56) / 0.16))
    hip_sway = (14 if 6.4 <= t < 8.96 else 5) * beat
    bounce = 2 * (1 - math.cos(2 * math.pi * t / 0.64))
    image = Image.new("RGB", (SIZE * SCALE, SIZE * SCALE), "#f6efe5")
    d = ImageDraw.Draw(image)

    def ellipse(box, fill, outline=None, width=1):
        d.ellipse(tuple(round(v * SCALE) for v in box), fill=fill,
                  outline=outline, width=width * SCALE)

    def line(points, fill, width):
        xy = [(round(x * SCALE), round(y * SCALE)) for x, y in points]
        d.line(xy, fill=fill, width=round(width * SCALE), joint="curve")
        r = width / 2
        for x, y in (points[0], points[-1]):
            ellipse((x - r, y - r, x + r, y + r), fill)

    def polygon(points, fill):
        d.polygon([(round(x * SCALE), round(y * SCALE)) for x, y in points], fill=fill)

    def text(position, value, size, color):
        d.text(tuple(v * SCALE for v in position), value, font=font(size),
               fill=color, anchor="mm")

    def project(p):
        x, y, z = p
        return (240 + x * math.cos(yaw) + z * math.sin(yaw),
                264 + y + bounce)

    def depth(p):
        return -p[0] * math.sin(yaw) + p[2] * math.cos(yaw)

    def bone(a, b, color, width):
        line([project(a), project(b)], INK, width + 3)
        line([project(a), project(b)], color, width)

    # Décor fixe et repères rythmiques.
    ellipse((48, 362, 432, 422), "#e9dfd1")
    ellipse((149, 374, 333, 398), "#d4c6b8")
    draw_first_name(d, first_name)
    text((240, 76), "ON SUIT LE RYTHME !", 11, "#79716c")
    for j in range(8):
        x = 170 + j * 20
        ellipse((x - 3, 104, x + 3, 110), SHIRT if j == int(t / 0.64) % 8 else "#ddd2c5")

    hip = (hip_sway, 28, 0)
    legs = []
    for side in (-1, 1):
        thigh = (hip_sway + side * 19, 40, 0)
        knee = (side * 27 + hip_sway * 0.4, 82 + side * beat * 2, 0)
        ankle = (side * 35, 116, 0)
        legs.append((depth(thigh), thigh, knee, ankle))
    for _, thigh, knee, ankle in sorted(legs):
        bone(thigh, knee, SKIN, 19)
        bone(knee, ankle, SKIN, 16)
        foot = project((ankle[0], ankle[1] + 8, 8))
        ellipse((foot[0] - 16, foot[1] - 7, foot[0] + 17, foot[1] + 8), INK)
        line([(foot[0] - 12, foot[1] + 6), (foot[0] + 13, foot[1] + 6)], "#fffaf3", 3)

    arms = []
    for side in (-1, 1):
        if t < 5.12:
            step = min(7, int(t / 0.64))
            progress = smooth((t % 0.64) / 0.42)
            prev = max(0, step - (1 if side == -1 else 2))
            nxt = max(0, step + (1 if side == -1 else 0))
            elbow, hand = [mix(a, b, progress) for a, b in zip(POSES[prev], POSES[nxt])]
        else:
            elbow, hand = POSES[-1]
            if t >= 8.96:
                w = smooth((t - 8.96) / 0.64)
                elbow, hand = mix(elbow, POSES[0][0], w), mix(hand, POSES[0][1], w)
        mirror = -side
        elbow = (elbow[0] * mirror + hip_sway * 0.25, elbow[1], elbow[2])
        hand = (hand[0] * mirror + hip_sway * 0.5, hand[1], hand[2])
        shoulder = (side * 32 + hip_sway * 0.2, -69, 0)
        arms.append((depth(elbow), shoulder, elbow, hand))

    def arm(item):
        _, shoulder, elbow, hand = item
        bone(shoulder, elbow, SKIN, 15)
        bone(shoulder, mix(shoulder, elbow, 0.42), SHIRT, 19)
        bone(elbow, hand, SKIN, 13)

    for item in sorted(arms):
        if item[0] < -4:
            arm(item)

    # Short rectangulaire de face ; silhouette de dos conservée.
    shorts_color = SHORTS_RED if tongue > 0 else SHORTS
    if math.cos(yaw) > 0:
        front = [project((hip_sway + x, y, 0)) for x, y in
                 ((-35, 0), (35, 0), (35, 55), (5, 55),
                  (5, 33), (-5, 33), (-5, 55), (-35, 55))]
        polygon(front, shorts_color)
        line(front + [front[0]], INK, 2)
    else:
        left = project((hip_sway - 21, 28, 0))
        right = project((hip_sway + 21, 28, 0))
        for x, y in (left, right):
            ellipse((x - 23, y - 17, x + 23, y + 29), shorts_color, INK, 2)
    polygon([project((hip_sway - 35, 0, 0)), project((hip_sway + 35, 0, 0)),
             project((hip_sway + 36, 31, 0)), project((hip_sway - 36, 31, 0))], shorts_color)
    if math.cos(yaw) < -0.5 and tongue <= 0:
        for side in (-1, 1):
            p = project((hip_sway + side * 20, 20, -20))
            pocket = [(p[0] - 6, p[1]), (p[0], p[1] + 5), (p[0] + 6, p[1])]
            line(pocket, "#b3a5e5", 2)

    torso = [(-31, -76, 0), (31, -76, 0), (36, -56, 0),
             (hip_sway + 29, 8, 0), (hip_sway - 29, 8, 0), (-36, -56, 0)]
    polygon([project(p) for p in torso], INK)
    polygon([project((x * 0.94, y + 1, z)) for x, y, z in torso], SHIRT)
    if math.cos(yaw) > 0.4:
        star = project((0, -42, 18))
        text(star, "★", 22, "#fff4d6")
    bone((0, -76, 0), (0, -91, 0), SKIN, 18)
    hx, hy = project((hip_sway * 0.1, -115, 0))
    hx += 9 * look_back

    def head_point(x, y, z):
        return (hx + x * math.cos(head_yaw) + z * math.sin(head_yaw), hy + y)

    ellipse((hx - 27, hy - 34, hx + 27, hy + 30), SKIN, INK, 2)
    if math.cos(head_yaw) > 0.2:
        if face is not None:
            # Centrage dans l'ellipse intérieure ; profondeur Z inchangée.
            paste_face(image, face, head_point(0, -2, 6), head_yaw)
        else:
            for side in (-1, 1):
                eye = head_point(side * 9, 0, 25)
                ellipse((eye[0] - 2, eye[1] - 3, eye[0] + 2, eye[1] + 2), INK)
        mouth = head_point(0, 12, 26)
        if tongue > 0:
            mx, my = mouth
            ellipse((mx - 8, my - 4, mx + 8, my + 6), INK)
            ellipse((mx - 5, my, mx + 5, my + 3 + 12 * tongue), "#f07596", INK, 1)
            line([(mx, my + 3), (mx, my + 3 + 7 * tongue)], "#b94068", 1)
        elif face is None:
            d.arc(tuple(round(v * SCALE) for v in
                        (mouth[0] - 7, mouth[1] - 5, mouth[0] + 7, mouth[1] + 4)),
                  0, 180, fill=INK, width=2 * SCALE)
    else:
        # Masse arrière effilée vers la nuque, sans calotte elliptique.
        back_hair = [(-23, -34), (-26, -20), (-24, -4),
                     (-17, 3), (-10, 1), (-3, 6), (5, 2),
                     (13, 4), (22, -3), (26, -19), (23, -34)]
        polygon([(hx + x, hy + y) for x, y in back_hair], INK)
    # Mèches asymétriques en éventail ; implantation au-dessus du portrait.
    hair_y = hy + (5 if math.cos(head_yaw) > 0.2 else 0)
    hair = [(-23, -33), (-29, -39), (-36, -48), (-22, -43),
            (-27, -58), (-12, -48), (-10, -63), (-1, -49),
            (7, -61), (10, -47), (24, -55), (21, -43),
            (34, -47), (27, -37), (23, -33), (12, -34),
            (2, -33), (-10, -34)]
    polygon([(hx + x, hair_y + y) for x, y in hair], INK)
    # Fermer le raccord au-dessus du front avec une implantation peu profonde.
    hairline = [(-23, -35), (23, -35), (20, -30), (10, -31),
                (0, -30), (-10, -31), (-20, -30)]
    polygon([(hx + x, hair_y + y) for x, y in hairline], INK)
    # Raccorder l'éventail aux tempes sans empiéter sur le centre du visage.
    temple_hair = [(21, -35), (26, -36), (29, -30), (30, -24),
                   (28, -17), (26, -21), (25, -13), (20, -13),
                   (16, -30)]
    for side in (-1, 1):
        polygon([(hx + side * x, hair_y + y) for x, y in temple_hair], INK)
    for item in sorted(arms):
        if item[0] >= -4:
            arm(item)

    label = "LES BRAS · LES ÉPAULES · LES HANCHES"
    if 5.12 <= t < 6.4:
        label = "ET ON TOURNE !"
    elif 6.4 <= t < 8.96:
        label = "ON SE DÉHANCHE !"
    text((240, 447), label, 12, INK)
    return image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def main():
    first_name = load_first_name()
    face = load_optional_face()
    frames = [render(i, first_name, face) for i in range(FRAMES)]
    # Une palette commune évite le scintillement des couleurs entre images.
    # Inclure la grimace finale pour conserver aussi le rose de la langue.
    samples = Image.new("RGB", (SIZE * 4, SIZE))
    for column, index in enumerate((0, 160, 195, 205)):
        samples.paste(frames[index], (column * SIZE, 0))
    palette = samples.quantize(colors=240 if face is not None else 128,
                               method=Image.Quantize.MEDIANCUT)
    # Réserver ces teintes rares : la langue occupe peu de pixels du décor.
    colors = palette.getpalette()
    colors.extend([0] * (768 - len(colors)))
    colors[384:390] = [240, 117, 150, 185, 64, 104]
    colors[390:393] = list(bytes.fromhex(SHORTS_RED.lstrip("#")))
    palette.putpalette(colors)
    frames = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    frames[0].save(OUT, save_all=True, append_images=frames[1:],
                   duration=1000 // FPS, loop=0, disposal=2, optimize=False)
    with Image.open(OUT) as gif:
        assert gif.size == (SIZE, SIZE)
        assert gif.n_frames == FRAMES
        assert gif.info["loop"] == 0
        for i in range(gif.n_frames):
            gif.seek(i)
            gif.load()
        print(f"Créé : {OUT} — {gif.n_frames} images, {FRAMES / FPS:.1f} s")


if __name__ == "__main__":
    main()
