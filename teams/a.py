import random
from teams.helper_function import Troops, Utils

team_name = "Segfaulters"
troops = [
    Troops.wizard, Troops.minion, Troops.archer, Troops.prince,
    Troops.dragon, Troops.skeleton, Troops.valkyrie, Troops.barbarian
]
deploy_list = Troops([])
team_signal = "h,_,_,_,_,_,_,_,_,10,-"

def random_x(min_val=-25, max_val=25):
    return random.randint(min_val, max_val)

def deploy(arena_data: dict):
    """
    DON'T TEMPER DEPLOY FUNCTION
    """
    deploy_list.list_ = []
    logic(arena_data)
    return deploy_list.list_, team_signal

def logic(arena_data: dict):
    global team_signal
    troops_data = Troops.troops_data
    my_tower = arena_data["MyTower"]
    opp_tower = arena_data["OppTower"]
    my_troops = arena_data["MyTroops"]
    opp_troops = arena_data["OppTroops"]
    # Our team signal stores the total troops the opponent has, the elixir of the opponent, and the current troops of the opponent. Its length won't exceed 180 if it runs according to plan.
    # --- Update Team Signal ---
    # This stores the total troops of the opponent, keeping them in order in which they were first deployed.
    changed = 0
    changed_name = ""
    for troop in opp_troops:
        current_names = [name.strip() for name in team_signal.split(",")] if team_signal else []
        if troop.name not in current_names[1:9] and "_" in current_names[1:9]:
            changed += 1
            j=0
            for i in range(1,10):
                if current_names[i]!="_":
                    j+=i
                    break
            if j!=1:
                for i in range(j,9):
                    current_names[i-1]=current_names[i]
                current_names[8]=troop.name
                changed_name += troop.name
        team_signal = ",".join(current_names)
    changed_elixir = 0
    #print(f"Team Signal: {team_signal}")
    current_troops=[]
    # This stores the current troops of the opponent
    for troop in opp_troops:
        if troop.name not in current_troops or (troop.name != current_troops[-1]):
            current_troops += [troop.name]
    # This calculates and stores the elixir of the opponent
    elixir_rate = 0.05 # given in the whatsapp group
    if my_tower.game_timer >= 1200:
        elixir_rate += 0.05 # given in the whatsapp group
    team = team_signal.split(",")
    team[9] = float(team[9])
    if len(current_troops)>0 and (team[10].split(".")[-1]!=current_troops[-1] and (len(team[10])<=len(".".join(current_troops)) or team[10].split(".")[:-1]!=current_troops)):
        changed_elixir+=troops_data[current_troops[-1]].elixir
    team[10] = ".".join(current_troops)
    team[9] -= changed_elixir
    team[9] += elixir_rate
    opp_elixir = team[9]
    team[9] = str(team[9])
    team_signal = ",".join(team)
    '''print("Opp_elixir:", opp_elixir)
    print("Game-timer:", my_tower.game_timer)
    if my_tower.game_timer%100 == 0:
        print(my_tower.total_elixir, my_tower.game_timer)'''


    # --- Analyze Opponent's Deck Composition ---

    # Strategies
    # 1. Counter air with ground, ground with air - attack mode - already done for us heh.
    # 2. Promote attack or defence? Depending on opponent troop position and elixir, and our tower health.
    # 3. Where to deploy troops? Depending on mode (attack/defence), opponent troop position and troop purpose.
    
    # Strategy 1
    opponent_air = {"Minion", "Dragon", "Musketeer", "Wizard", "Archer"}
    opponent_ground = {"Prince", "Knight", "Barbarian", "Valkyrie", "Skeleton"}
    
    tokens = [token.strip() for token in team_signal.split(",") if token.strip() != "h"] # This still works because the other things in the team signal cannot match a troop name
    count_air = sum(1 for token in tokens if token in opponent_air)
    count_ground = sum(1 for token in tokens if token in opponent_ground)
     
    if count_ground > count_air:
        recommended_counter = "air"    # Counter ground with air units.
    elif count_air > count_ground:
        recommended_counter = "ground" # Counter air with ground units.
    else:
        recommended_counter = None     # No clear preference.
    danger = 0
    # Strategy 2
    scale = 0
    direction=0
    for troop in opp_troops:
        if troop.position[1] < 60:
            scale += 1
            if troop==Troops.wizard:
                scale+=2
            if troop.position[0] < -10:
                direction-=1
            elif troop.position[0] > 10:
                direction+=1
        if troop.position[1] < 40:
            scale += 2
            danger += 1
        
    if opp_elixir > 3:
        scale += 1
    elif opp_elixir < 1:
        scale -= 1
    if my_tower.health < opp_tower.health:
        scale += 1
    if my_tower.health < 3516:
        scale += 1
    elif opp_tower.health < 1758:
        scale -= 1
    
    if scale >= 3:
        mode = "defence"
    elif scale <= 2:
        mode = "attack"
    else:
        mode = None
    print(my_tower.game_timer,mode,my_tower.total_elixir, opp_elixir)
    
    # Strategy 3


    # --- Score Our Troops (only from deployable troops) ---
    deployable = my_tower.deployable_troops
    print(deployable,team_signal)
    # Define base scores and categories for our troops.
    troop_data = {
        Troops.wizard:    {"score": 7, "category": "air", "mode": "either", "name": "Wizard"},
        Troops.minion:    {"score": 2, "category": "air", "mode" : "attack"  , "name": "Minion"},
        Troops.prince:    {"score": 3, "category": "ground", "mode":"attack","name": "Prince"},
        Troops.archer:     {"score": 4, "category": "air", "mode" : "either" ,"name": "Archer"},
        Troops.dragon:    {"score": 6, "category": "air", "mode":"either", "name": "Dragon"},
        Troops.skeleton:  {"score": 3, "category": "ground", "mode":"defence","name": "Skeleton"},
        Troops.valkyrie:   {"score": 4, "category": "air", "mode":"either","name": "Valkyrie"},
        Troops.barbarian: {"score": 3, "category": "ground", "mode":"defence", "name": "Barbarian"}
    }
    
    bonus_category = 2  # Bonus for matching the recommended counter strategy.
    bonus_mode = 1 # For matching the required mode
    best_troop = None
    best_score = -1
    
    # Loop over our full troop list, but only consider those that are deployable.
    for troop in troops:
        if troop not in deployable:
            continue
        base = troop_data[troop]["score"]
        cat = troop_data[troop]["category"]
        mod = troop_data[troop]["mode"]
        score = base + (bonus_category if recommended_counter and cat == recommended_counter else 0) + (bonus_mode if mode and mod==(mode or "either") else 0)
        
        # Only wizard can effectively beat the wizard at any cost. The Valkyrie+Wizard combo appears to be deadly.
        if "wizard" in team_signal.split(",")[10]:
            if troop_data[troop]["name"]=="Valkyrie" or troop_data[troop]["name"]=="Wizard":
                score+=2
            if troop_data[troop]["name"]=="Prince":
                score-=1
        else:
            if troop_data[troop]["name"]=="Prince":
                score+=1
        # In defence mode, we want to preserve elixir
        if mode=="defence":
            if troops_data[troop_data[troop]["name"]].elixir==5:
                if danger>=3 and my_tower.total_elixir < 4.05:
                    score -= 1
            if troops_data[troop_data[troop]["name"]].elixir==3:
                score += 1
            if "wizard" in team_signal.split(",")[10] and opp_troops[Troops.wizard].position[1]<50:
                if troop_data[troop]["name"]=="Skeleton":
                    score += 1
        print(troop_data[troop]["name"],score)
        if score > best_score:
            best_score = score
            best_troop = troop

    if my_tower.game_timer < 10:
        if Troops.dragon in deployable and Troops.wizard in deployable:
            deploy_list.list_.append((Troops.dragon, (0, 40)))
            deploy_list.list_.append((Troops.wizard, (0, 35)))

    if "wizard" in team_signal.split(",")[10] and opp_troops[Troops.wizard].position[1]<80:
        if Troops.archer in deployable and Troops.barbarian in deployable:
            deploy_list.list_.append((Troops.archer,(random_x(opp_troops[Troops.wizard].position[0]-5,opp_troops[Troops.wizard].position[0]+5)),30))
            deploy_list.list_.append((Troops.barbarian,(random_x(opp_troops[Troops.wizard].position[0]-5,opp_troops[Troops.wizard].position[0]+5)),25))
        elif Troops.valkyrie in deployable:
            deploy_list.list_.append((Troops.valkyrie,(random_x(opp_troops[Troops.wizard].position[0]-5,opp_troops[Troops.wizard].position[0]+5)),45))
    if "dragon" in team_signal.split(",")[10] and opp_troops[Troops.dragon].position[1]<=50:
        if Troops.minion in deployable:
            deploy_list.list_.append((Troops.minion,(random_x(opp_troops[Troops.dragon].position[0]-5,opp_troops[Troops.dragon].position[0]+5)),30))
    if ("wizard" in team_signal.split(",")[10] and opp_troops[Troops.wizard].position[1]<35) or ("dragon" in team_signal.split(",")[10] and opp_troops[Troops.dragon].position[1]<35) or ("prince" in team_signal.split(",")[10] and opp_troops[Troops.prince].position[1]<35) or ("musketeer" in team_signal.split(",")[10] and opp_troops[Troops.musketeer].position[1]<35) or ("valkyrie" in team_signal.split(",")[10] and opp_troops[Troops.valkyrie].position[1]<35):
        if Troops.wizard in deployable:
            deploy_list.list_.append((Troops.wizard,(0,45)))
        elif Troops.minion in deployable:
            deploy_list.list_.append((Troops.minion,(0,45)))

        
    # --- Deployment Position ---
    elif best_troop is not None:
        selected_category = troop_data[best_troop]["category"]
        if my_tower.game_timer < 100:
            deploy_position = (random_x(-25, 25), 40)
        elif selected_category == "air":
            if mode=="attack":
                if direction<0:
                    deploy_position = (random_x(-25, 0), 20)
                elif direction>0:
                    deploy_position = (random_x(0, 25), 20)
                else:
                    deploy_position = (random_x(-25, 25), 20)
            else:
                if direction<0:
                    deploy_position = (random_x(-15, 0), 10)
                elif direction>0:
                    deploy_position = (random_x(0, 15), 10)
                else:
                    deploy_position = (random_x(-15, 15), 10)
        else:
            # Deploy ground units slightly closer for support.
            if troop_data[best_troop]["name"]=="Valkyrie":
                deploy_position = (0,20)
                if Troops.dragon in deployable:
                    deploy_list.list_.append((Troops.dragon, (0,0)))
                if Troops.wizard in deployable:
                    deploy_list.list_.append((Troops.wizard, (0,0)))
            if mode=="attack":
                if direction<0:
                    deploy_position = (random_x(-10, 0), 20)
                elif direction>0:
                    deploy_position = (random_x(0, 10), 20)
                else:
                    deploy_position = (random_x(-10, 10), 20)
            else:
                if direction<0:
                    deploy_position = (random_x(-10, 5), 10)
                elif direction>0:
                    deploy_position = (random_x(5, 10), 10)
                else:
                    deploy_position = (random_x(-10, 10), 10)
        deploy_list.list_.append((best_troop, deploy_position))
    else:
        # Fallback: If no deployable troop meets criteria, deploy the first available troop.
        if deployable:
            deploy_list.list_.append((deployable[0], (0, 0)))
