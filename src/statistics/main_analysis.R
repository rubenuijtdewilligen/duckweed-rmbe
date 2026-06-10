library(tidyverse)
library(readxl)

dir.create("output/plots/", recursive = TRUE, showWarnings = FALSE)

df_duckweed <- read_excel("data/daily_measurements.xlsx")

df_duckweed <- df_duckweed %>%
  mutate(
    treatment = case_when(
      container_id %in% c(3, 4) ~ "Low light intensity",
      container_id %in% c(7, 8) ~ "High light intensity",
      TRUE ~ "unknown"
    )
  )

print(head(df_duckweed))

anova_cover <- aov(coverage_percent ~ treatment * as.factor(days_since_start) + Error(as.factor(container_id)), data = df_duckweed)
print(summary(anova_cover))

df_cover_summary <- df_duckweed %>%
  group_by(treatment, days_since_start) %>%
  summarise(
    Mean_Coverage = mean(coverage_percent),
    SEM_Coverage  = sd(coverage_percent) / sqrt(n()),
    .groups = "drop"
  )

plot_coverage <- ggplot(df_cover_summary, aes(x = days_since_start, y = Mean_Coverage, color = treatment, group = treatment)) +
  geom_line(linewidth = 1) +
  geom_point(size = 3) +
  geom_errorbar(aes(ymin = Mean_Coverage - SEM_Coverage, ymax = Mean_Coverage + SEM_Coverage), width = 0.15) +
  scale_color_manual(values = c("Low light intensity" = "#74c476", "High light intensity" = "#238b45")) +
  scale_x_continuous(breaks = unique(df_duckweed$days_since_start)) +
  labs(
    title = "Duckweed Surface Area Coverage Over Time",
    x = "Days Since Start",
    y = "Surface Coverage (%)",
    color = "Treatment"
  ) +
  theme_minimal() +
  theme(panel.grid.minor = element_blank())

ggsave("output/plots/plot_coverage.png", plot = plot_coverage, width = 6, height = 4, dpi = 300)

most_recent_day <- max(df_duckweed$days_since_start)
df_latest <- df_duckweed %>% filter(days_since_start == most_recent_day)

wilcox_bleach <- wilcox.test(bleaching_score ~ treatment, data = df_latest, exact = FALSE)
print(wilcox_bleach)

df_bleach_summary <- df_duckweed %>%
  group_by(treatment, days_since_start) %>%
  summarise(
    Mean_Bleaching = mean(bleaching_score),
    SEM_Bleaching  = sd(bleaching_score) / sqrt(n()),
    .groups = "drop"
  )

df_bleach_summary[is.na(df_bleach_summary)] <- 0

plot_bleaching <- ggplot(df_bleach_summary, aes(x = days_since_start, y = Mean_Bleaching, color = treatment, group = treatment)) +
  geom_line(linewidth = 1) +
  geom_point(size = 3) +
  geom_errorbar(aes(ymin = Mean_Bleaching - SEM_Bleaching, ymax = Mean_Bleaching + SEM_Bleaching), width = 0.15) +
  scale_color_manual(values = c("Low light intensity" = "#74c476", "High light intensity" = "#238b45")) +
  scale_x_continuous(breaks = unique(df_duckweed$days_since_start)) +
  scale_y_continuous(limits = c(0, 5)) +
  labs(
    title = "Duckweed Bleaching Score Over Time",
    subtitle = "Score: 0 (healthy) to 5 (completely bleached)",
    x = "Days Since Start",
    y = "Mean Bleaching Score",
    color = "Treatment"
  ) +
  theme_minimal() +
  theme(panel.grid.minor = element_blank())

ggsave("output/plots/plot_bleaching.png", plot = plot_bleaching, width = 6, height = 4, dpi = 300)