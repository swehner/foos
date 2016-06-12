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
    if any([k in line for k in goalmap.keys()]):
        parts = line.split()
        data = {'source': 'serial', 'team': goalmap[parts[0]]}

        if len(parts) > 1:
            data['duration'] = int(parts[1])

        if len(parts) > 2:
            data['elapsed'] = int(parts[2])

        return 'goal_event', data

    if '_' in line:
        btn, state = line.split('_')
        btn = btnmap.get(btn, 'ERROR')
        state = statemap.get(state, 'ERROR')
        return 'button_event', {'source': 'serial', 'btn': btn, 'state': state}

    return None
