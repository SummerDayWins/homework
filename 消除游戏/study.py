# -*- coding: utf-8 -*-
import pygame
import random
import time
import math
import os
# 初始化Pygame
pygame.init()

# 设置窗口大小
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 600
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("连连看游戏")

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# 游戏参数
GRID_SIZE = 8
TILE_SIZE = 70
MARGIN = 5
TOTAL_TIME = 180  # 3分钟倒计时
LAYERS = 3  # 设置层数

# 加载图案
patterns = [pygame.image.load(f"pattern_{i}.png") for i in range(1, 9)]
patterns = [pygame.transform.scale(pattern, (TILE_SIZE, TILE_SIZE)) for pattern in patterns]


# 创建游戏板
def create_board():
    board = [[[0 for _ in range(LAYERS)] for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    pattern_pairs = list(range(1, 9)) * (GRID_SIZE * GRID_SIZE * LAYERS // 8)
    random.shuffle(pattern_pairs)
    for layer in range(LAYERS):
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                board[i][j][layer] = pattern_pairs.pop()
    return board


# 绘制游戏板
def draw_board(board):
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            x = j * (TILE_SIZE + MARGIN) + MARGIN
            y = i * (TILE_SIZE + MARGIN) + MARGIN
            for layer in range(LAYERS):
                if board[i][j][layer] != 0:
                    screen.blit(patterns[board[i][j][layer] - 1], (x, y - layer * 5))
                    break  # 只绘制最上层的非零图案


# 检查两个图案是否可以连接
def can_connect(board, pos1, pos2):
    i1, j1 = pos1
    i2, j2 = pos2
    pattern1 = get_top_pattern(board, i1, j1)
    pattern2 = get_top_pattern(board, i2, j2)
    return pattern1 == pattern2 and pattern1 != 0 and not (i1 == i2 and j1 == j2)

# 获取一个位置最上层的非零图案
def get_top_pattern(board, i, j):
    for layer in range(LAYERS):
        if board[i][j][layer] != 0:
            return board[i][j][layer]
    return 0

# 移除匹配的图案
def remove_pattern(board, pos):
    i, j = pos
    for layer in range(LAYERS):
        if board[i][j][layer] != 0:
            board[i][j][layer] = 0
            break

# 读取历史最高连击数
def read_highest_combo():
    if os.path.exists("highest_combo.txt"):
        with open("highest_combo.txt", "r") as f:
            return int(f.read())
    return 0

# 保存历史最高连击数
def save_highest_combo(combo):
    with open("highest_combo.txt", "w") as f:
        f.write(str(combo))

# 主游戏循环
def game_loop():
    board = create_board()
    selected = None
    start_time = time.time()
    paused = False
    pause_start_time = 0
    shake_offset = 0
    not_match_message = None
    not_match_time = 0
    combo_count = 0
    max_combo_count = 0
    last_match_time = 0
    combo_message = None
    combo_time = 0
    highest_combo = read_highest_combo()

    while True:
        current_time = time.time()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = not paused
                    if paused:
                        pause_start_time = current_time
                    else:
                        start_time += current_time - pause_start_time
            if not paused:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    i = y // (TILE_SIZE + MARGIN)
                    j = x // (TILE_SIZE + MARGIN)
                    if 0 <= i < GRID_SIZE and 0 <= j < GRID_SIZE:
                        if selected is None:
                            if get_top_pattern(board, i, j) != 0:
                                selected = (i, j)
                        else:
                            if can_connect(board, selected, (i, j)):
                                remove_pattern(board, selected)
                                remove_pattern(board, (i, j))
                                # 检测连击
                                if current_time - last_match_time < 1.5:  # 1.5秒内的消除算作连击
                                    combo_count += 1
                                else:
                                    combo_count = 1
                                last_match_time = current_time
                                if combo_count > 1:
                                    combo_message = f"COMBO x{combo_count}!"
                                    combo_time = current_time
                                max_combo_count = max(max_combo_count, combo_count)
                                if max_combo_count > highest_combo:
                                    highest_combo = max_combo_count
                                    save_highest_combo(highest_combo)
                            else:
                                not_match_message = "NOT MATCH!!!"
                                not_match_time = current_time
                                combo_count = 0
                            selected = None

        if paused:
            font = pygame.font.Font(None, 48)
            pause_text = font.render("Paused", True, BLACK)
            screen.blit(pause_text, (WINDOW_WIDTH // 2 - pause_text.get_width() // 2, WINDOW_HEIGHT // 2))
            pygame.display.flip()
            continue

        screen.fill(WHITE)
        draw_board(board)

        if selected:
            i, j = selected
            # 计算抖动偏移量
            shake_offset = math.sin(current_time * 20) * 2
            rect = pygame.Rect(
                j * (TILE_SIZE + MARGIN) + MARGIN + shake_offset,
                i * (TILE_SIZE + MARGIN) + MARGIN + shake_offset,
                TILE_SIZE,
                TILE_SIZE
            )
            pygame.draw.rect(screen, RED, rect, 3)  # 绘制红色边框,宽度为3像素

            # 重新绘制选中的方块，使其显示在边框上方
            x = j * (TILE_SIZE + MARGIN) + MARGIN + shake_offset
            y = i * (TILE_SIZE + MARGIN) + MARGIN + shake_offset
            pattern = get_top_pattern(board, i, j)
            if pattern != 0:
                screen.blit(patterns[pattern - 1], (x, y))

        # 显示不匹配消息
        if not_match_message and current_time - not_match_time < 0.5:
            font = pygame.font.Font(None, 36)
            text = font.render(not_match_message, True, RED)
            mouse_pos = pygame.mouse.get_pos()
            screen.blit(text, (mouse_pos[0] + 10, mouse_pos[1] + 10))
        else:
            not_match_message = None

        # 显示连击消息
        if combo_message and current_time - combo_time < 1.0:
            font = pygame.font.Font(None, 48)
            text = font.render(combo_message, True, (255, 165, 0))  # 橙色
            mouse_pos = pygame.mouse.get_pos()
            screen.blit(text, (mouse_pos[0] + 10, mouse_pos[1] - 40))
        else:
            combo_message = None

        # 显示当前最高连击和历史最高连击
        font = pygame.font.Font(None, 24)
        max_combo_text = font.render(f"Max Combo This Game: {max_combo_count}", True, BLACK)
        highest_combo_text = font.render(f"All-Time Highest Combo: {highest_combo}", True, BLACK)
        screen.blit(max_combo_text, (10, 40))
        screen.blit(highest_combo_text, (10, 70))

        # 绘制倒计时
        elapsed_time = int(current_time - start_time)
        remaining_time = max(0, TOTAL_TIME - elapsed_time)
        font = pygame.font.Font(None, 36)
        time_text = font.render(f"Time Left: {remaining_time}Seconds", True, BLACK)
        screen.blit(time_text, (10, 10))

        pygame.display.flip()

        # 检查游戏是否结束
        if remaining_time == 0:
            return False, max_combo_count  # 游戏失败
        elif all(all(all(tile == 0 for tile in column) for column in row) for row in board):
            return True, max_combo_count  # 游戏成功


# 主菜单
def main_menu():
    font = pygame.font.Font(None, 48)
    title = font.render("THE GAME", True, BLACK)
    start_text = font.render("START", True, BLACK)
    quit_text = font.render("EXIT", True, BLACK)

    while True:
        screen.fill(WHITE)
        screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 100))
        screen.blit(start_text, (WINDOW_WIDTH // 2 - start_text.get_width() // 2, 300))
        screen.blit(quit_text, (WINDOW_WIDTH // 2 - quit_text.get_width() // 2, 400))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if WINDOW_WIDTH // 2 - start_text.get_width() // 2 < x < WINDOW_WIDTH // 2 + start_text.get_width() // 2:
                    if 300 < y < 300 + start_text.get_height():
                        return True
                if WINDOW_WIDTH // 2 - quit_text.get_width() // 2 < x < WINDOW_WIDTH // 2 + quit_text.get_width() // 2:
                    if 400 < y < 400 + quit_text.get_height():
                        return False

        pygame.display.flip()


# 游戏结束界面
def game_over(success, max_combo):
    font = pygame.font.Font(None, 48)
    if success:
        game_over_text = font.render("SUCCESS!", True, (0, 255, 0))  # 绿色
    else:
        game_over_text = font.render("GAME OVER", True, RED)
    max_combo_text = font.render(f"Max Combo This Game: {max_combo}", True, BLACK)
    restart_text = font.render("RESTART", True, BLACK)
    quit_text = font.render("QUIT", True, BLACK)

    while True:
        screen.fill(WHITE)
        screen.blit(game_over_text, (WINDOW_WIDTH // 2 - game_over_text.get_width() // 2, 100))
        screen.blit(max_combo_text, (WINDOW_WIDTH // 2 - max_combo_text.get_width() // 2, 200))
        screen.blit(restart_text, (WINDOW_WIDTH // 2 - restart_text.get_width() // 2, 300))
        screen.blit(quit_text, (WINDOW_WIDTH // 2 - quit_text.get_width() // 2, 400))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if WINDOW_WIDTH // 2 - restart_text.get_width() // 2 < x < WINDOW_WIDTH // 2 + restart_text.get_width() // 2:
                    if 300 < y < 300 + restart_text.get_height():
                        return True
                if WINDOW_WIDTH // 2 - quit_text.get_width() // 2 < x < WINDOW_WIDTH // 2 + quit_text.get_width() // 2:
                    if 400 < y < 400 + quit_text.get_height():
                        return False

        pygame.display.flip()


# 主程序
while True:
    if main_menu():
        game_result = game_loop()
        if not game_over(game_result[0], game_result[1]):
            break
    else:
        break

pygame.quit()
