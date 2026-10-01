import pygame
import random
import math
import wave
import io

from game.beat import Note, LANES, LANE_KEYS, LANE_LABELS, LANE_COLORS


WIDTH, HEIGHT = 480, 640
FPS = 60

HIT_Y = HEIGHT - 80
HIT_WINDOW = 30

BG = (15, 10, 25)

LANE_W = WIDTH // LANES


# -------------------------------------------------------------
# TASK 3: BPM SETTINGS
# -------------------------------------------------------------

BPM = 120

# Time between two beats, in seconds
BEAT_INTERVAL = 60 / BPM

# Hold notes must be held for 1 second
HOLD_DURATION = 1.0


class GameEngine:

    def __init__(self):

        pygame.init()
        pygame.mixer.init()

        # Create the hit sound after the mixer has been initialized
        self.hit_sound = self.create_hit_sound()

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT)
        )

        pygame.display.set_caption(
            "Rhythm Tap"
        )

        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont(
            "monospace",
            26,
            bold=True
        )

        self.big_font = pygame.font.SysFont(
            "monospace",
            44,
            bold=True
        )

        self.reset()

    # ---------------------------------------------------------
    # TASK 1: Generate a beep programmatically
    # ---------------------------------------------------------

    def create_hit_sound(self):

        sample_rate = 44100
        duration = 0.08
        frequency = 700

        num_samples = int(
            sample_rate * duration
        )

        samples = bytearray()

        for i in range(num_samples):

            value = int(
                32767
                * 0.4
                * math.sin(
                    2
                    * math.pi
                    * frequency
                    * i
                    / sample_rate
                )
            )

            samples.extend(
                value.to_bytes(
                    2,
                    byteorder="little",
                    signed=True
                )
            )

        sound_file = io.BytesIO()

        with wave.open(sound_file, "wb") as wav:

            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(samples)

        sound_file.seek(0)

        return pygame.mixer.Sound(
            file=sound_file
        )

    # ---------------------------------------------------------
    # RESET
    # ---------------------------------------------------------

    def reset(self):

        self.notes = []

        self.score = 0

        self.combo = 0

        self.max_combo = 0

        self.misses = 0

        # Restored existing note speed
        self.speed = 5

        self.frame = 0

        self.feedback = []

        self.game_over = False

        # -----------------------------------------------------
        # TASK 3: Time-based BPM spawning
        # -----------------------------------------------------

        self.last_spawn_time = pygame.time.get_ticks()

    # ---------------------------------------------------------
    # SPAWN NOTE
    # ---------------------------------------------------------

    def spawn_note(self):

        # Keep the existing random lane selection
        lane = random.randint(
            0,
            LANES - 1
        )

        # About 25% of notes are hold notes.
        is_hold = random.random() < 0.25

        self.notes.append(
            Note(
                lane,
                y=-30,
                speed=self.speed,
                is_hold=is_hold
            )
        )

    # ---------------------------------------------------------
    # HANDLE EVENTS
    # ---------------------------------------------------------

    def handle_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_r:

                    self.reset()

                elif not self.game_over:

                    for i, key in enumerate(
                        LANE_KEYS
                    ):

                        if event.key == key:

                            self.process_tap(i)

        return True

    # ---------------------------------------------------------
    # PROCESS TAP / START HOLD
    # ---------------------------------------------------------

    def process_tap(self, lane):

        # Find closest note in this lane near hit zone
        best = None

        best_dist = 9999

        for note in self.notes:

            if (
                note.lane == lane
                and not note.hit
                and not note.missed
            ):

                # For hold notes, use the top of the
                # note as the point that reaches the
                # hit zone.
                if note.is_hold:

                    note_position = note.y

                else:

                    note_position = (
                        note.y
                        + Note.HEIGHT // 2
                    )

                dist = abs(
                    note_position - HIT_Y
                )

                if dist < best_dist:

                    best_dist = dist
                    best = note

        lane_x = (
            lane * LANE_W
            + LANE_W // 2
        )

        # -----------------------------------------------------
        # NO NOTE NEAR HIT ZONE
        # -----------------------------------------------------

        if (
            not best
            or best_dist > HIT_WINDOW
        ):

            self.combo = 0

            self.feedback.append(
                [
                    "MISS",
                    (220, 60, 60),
                    40,
                    lane_x,
                    HIT_Y - 30
                ]
            )

            return

        # -----------------------------------------------------
        # HOLD NOTE
        # -----------------------------------------------------

        if best.is_hold:

            # Start the hold.
            # The note only scores after one full second.

            best.holding = True
            best.hold_time = 0

            self.feedback.append(
                [
                    "HOLD",
                    (180, 180, 255),
                    20,
                    lane_x,
                    HIT_Y - 30
                ]
            )

            return

        # -----------------------------------------------------
        # NORMAL TAP NOTE
        # -----------------------------------------------------

        best.hit = True

        if best_dist < 8:

            grade, pts = "PERFECT", 300

            col = (255, 220, 0)

        elif best_dist < 18:

            grade, pts = "GREAT", 200

            col = (100, 220, 100)

        else:

            grade, pts = "OK", 100

            col = (180, 180, 255)

        # Task 1 hit sound
        self.hit_sound.play()

        self.combo += 1

        self.max_combo = max(
            self.max_combo,
            self.combo
        )

        self.score += (
            pts
            * max(
                1,
                self.combo // 5
            )
        )

        self.feedback.append(
            [
                grade,
                col,
                40,
                lane_x,
                HIT_Y - 30
            ]
        )

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------

    def update(self):

        if self.game_over:
            return

        self.frame += 1

        # -----------------------------------------------------
        # TASK 3: BPM-SYNCHRONIZED SPAWNING
        # -----------------------------------------------------

        current_time = pygame.time.get_ticks()

        elapsed_time = (
            current_time
            - self.last_spawn_time
        ) / 1000.0

        if elapsed_time >= BEAT_INTERVAL:

            self.spawn_note()

            # Keep spawning synchronized to the beat timeline.
            self.last_spawn_time += int(
                BEAT_INTERVAL * 1000
            )

        # -----------------------------------------------------
        # UPDATE NOTES
        # -----------------------------------------------------

        for note in self.notes:

            note.update()

            # -------------------------------------------------
            # HOLD NOTE LOGIC
            # -------------------------------------------------

            if (
                note.is_hold
                and note.holding
            ):

                keys = pygame.key.get_pressed()

                required_key = LANE_KEYS[
                    note.lane
                ]

                if keys[required_key]:

                    note.hold_time += (
                        1 / FPS
                    )

                    if (
                        note.hold_time
                        >= HOLD_DURATION
                    ):

                        note.hit = True

                        note.holding = False

                        lane_x = (
                            note.lane
                            * LANE_W
                            + LANE_W // 2
                        )

                        pts = 100

                        self.combo += 1

                        self.max_combo = max(
                            self.max_combo,
                            self.combo
                        )

                        self.score += (
                            pts
                            * max(
                                1,
                                self.combo // 5
                            )
                        )

                        # Successful hold sound
                        self.hit_sound.play()

                        self.feedback.append(
                            [
                                "HOLD OK",
                                (180, 180, 255),
                                40,
                                lane_x,
                                HIT_Y - 30
                            ]
                        )

                else:

                    # Player released the key too early.
                    note.missed = True

                    note.holding = False

                    # Count failed hold as a miss.
                    self.misses += 1

                    # Reset combo.
                    self.combo = 0

                    lane_x = (
                        note.lane
                        * LANE_W
                        + LANE_W // 2
                    )

                    self.feedback.append(
                        [
                            "MISS",
                            (220, 60, 60),
                            40,
                            lane_x,
                            HIT_Y - 30
                        ]
                    )

                    continue

            # -------------------------------------------------
            # NORMAL NOTE / UNSTARTED HOLD NOTE MISSED
            # -------------------------------------------------

            if (
                not note.hit
                and not note.missed
                and not note.holding
                and note.y
                > HIT_Y
                + HIT_WINDOW
                + Note.HEIGHT
            ):

                note.missed = True

                self.misses += 1

                self.combo = 0

        # -----------------------------------------------------
        # REMOVE NOTES
        # -----------------------------------------------------

        self.notes = [
            n
            for n in self.notes
            if not (
                n.hit
                or (
                    n.missed
                    and n.y > HEIGHT + 10
                )
            )
        ]

        # -----------------------------------------------------
        # UPDATE FEEDBACK
        # -----------------------------------------------------

        self.feedback = [
            [
                t,
                c,
                ttl - 1,
                x,
                y
            ]
            for t, c, ttl, x, y
            in self.feedback
            if ttl > 1
        ]

        # -----------------------------------------------------
        # GAME OVER
        # -----------------------------------------------------

        if self.misses >= 15:

            self.game_over = True

    # ---------------------------------------------------------
    # DRAW
    # ---------------------------------------------------------

    def draw(self):

        self.screen.fill(BG)

        # -----------------------------------------------------
        # Lane dividers
        # -----------------------------------------------------

        for i in range(
            LANES + 1
        ):

            pygame.draw.line(
                self.screen,
                (40, 40, 60),
                (
                    i * LANE_W,
                    0
                ),
                (
                    i * LANE_W,
                    HEIGHT
                ),
                1
            )

        # -----------------------------------------------------
        # Hit line
        # -----------------------------------------------------

        pygame.draw.line(
            self.screen,
            (80, 80, 100),
            (
                0,
                HIT_Y
            ),
            (
                WIDTH,
                HIT_Y
            ),
            2
        )

        # -----------------------------------------------------
        # Lane labels / hit targets
        # -----------------------------------------------------

        for i in range(LANES):

            lx = (
                i * LANE_W
                + LANE_W // 2
            )

            pygame.draw.rect(
                self.screen,
                LANE_COLORS[i],
                pygame.Rect(
                    lx - Note.WIDTH // 2,
                    HIT_Y - 12,
                    Note.WIDTH,
                    24
                ),
                border_radius=6
            )

            lbl = self.font.render(
                LANE_LABELS[i],
                True,
                (20, 20, 20)
            )

            self.screen.blit(
                lbl,
                (
                    lx
                    - lbl.get_width() // 2,
                    HIT_Y - 10
                )
            )

        # -----------------------------------------------------
        # Notes
        # -----------------------------------------------------

        for note in self.notes:

            if note.hit:
                continue

            lx = (
                note.lane
                * LANE_W
                + LANE_W // 2
            )

            rect = note.get_rect(lx)

            pygame.draw.rect(
                self.screen,
                LANE_COLORS[note.lane],
                rect,
                border_radius=5
            )

            # Hold notes have an inner white line.
            if note.is_hold:

                pygame.draw.line(
                    self.screen,
                    (255, 255, 255),
                    (
                        rect.centerx,
                        rect.top + 5
                    ),
                    (
                        rect.centerx,
                        rect.bottom - 5
                    ),
                    3
                )

        # -----------------------------------------------------
        # Feedback
        # -----------------------------------------------------

        for (
            text,
            color,
            ttl,
            x,
            y
        ) in self.feedback:

            surf = self.font.render(
                text,
                True,
                color
            )

            alpha = min(
                255,
                ttl * 7
            )

            surf.set_alpha(alpha)

            self.screen.blit(
                surf,
                (
                    x
                    - surf.get_width() // 2,
                    y
                )
            )

        # -----------------------------------------------------
        # HUD
        # -----------------------------------------------------

        sc = self.font.render(
            f"Score: {self.score}",
            True,
            (220, 220, 220)
        )

        co = self.font.render(
            f"Combo: {self.combo}x",
            True,
            (255, 220, 80)
        )

        mi = self.font.render(
            f"Misses: {self.misses}/15",
            True,
            (220, 100, 100)
        )

        self.screen.blit(
            sc,
            (10, 10)
        )

        self.screen.blit(
            co,
            (10, 40)
        )

        self.screen.blit(
            mi,
            (
                WIDTH - 170,
                10
            )
        )

        # -----------------------------------------------------
        # GAME OVER
        # -----------------------------------------------------

        if self.game_over:

            ov = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )

            ov.fill(
                (0, 0, 0, 160)
            )

            self.screen.blit(
                ov,
                (0, 0)
            )

            msg = self.big_font.render(
                "GAME OVER",
                True,
                (220, 60, 60)
            )

            sc_msg = self.font.render(
                f"Final Score: {self.score}  "
                f"Max Combo: {self.max_combo}x",
                True,
                (200, 200, 200)
            )

            restart = self.font.render(
                "Press R to Restart",
                True,
                (160, 160, 160)
            )

            self.screen.blit(
                msg,
                (
                    WIDTH // 2
                    - msg.get_width() // 2,
                    HEIGHT // 2 - 70
                )
            )

            self.screen.blit(
                sc_msg,
                (
                    WIDTH // 2
                    - sc_msg.get_width() // 2,
                    HEIGHT // 2
                )
            )

            self.screen.blit(
                restart,
                (
                    WIDTH // 2
                    - restart.get_width() // 2,
                    HEIGHT // 2 + 50
                )
            )

        pygame.display.flip()

    # ---------------------------------------------------------
    # RUN
    # ---------------------------------------------------------

    def run(self):

        running = True

        while running:

            running = self.handle_events()

            self.update()

            self.draw()

            self.clock.tick(FPS)

        pygame.quit()