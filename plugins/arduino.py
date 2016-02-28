btnmap = {
    "YD": "yellow_minus",
    "YI": "yellow_plus",
    "OK": "ok",
    "BD": "black_minus",
    "BI": "black_plus"
}

statemap = {
    "U": "up",
    "D": "down"
}

goalmap = {
    "YG": "yellow",
    "BG": "black"
}


def getEventForButton(line):
    if line in goalmap:
        return 'goal_event', {'source': 'serial', 'team': goalmap[line]}

    if '_' in line:
        btn, state = line.split('_')
        btn = btnmap.get(btn, 'ERROR')
        state = statemap.get(state, 'ERROR')
        return 'button_event', {'source': 'serial', 'btn': btn, 'state': state}

    return None
