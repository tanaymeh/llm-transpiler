class CandyLCHard:
    def count(self, n):
        return (n * (n + 1)) // 2

    def candy(self, ratings):
        if len(ratings) <= 1:
            return len(ratings)

        candies = 0
        up = 0
        down = 0
        oldSlope = 0

        for i in range(1, len(ratings)):
            newSlope = (
                1
                if ratings[i] > ratings[i - 1]
                else (-1 if ratings[i] < ratings[i - 1] else 0)
            )

            if (oldSlope > 0 and newSlope == 0) or (oldSlope < 0 and newSlope >= 0):
                candies += self.count(up) + self.count(down) + max(up, down)
                up = 0
                down = 0

            if newSlope > 0:
                up += 1
            elif newSlope < 0:
                down += 1
            else:
                candies += 1

            oldSlope = newSlope

        candies += self.count(up) + self.count(down) + max(up, down) + 1
        return candies
