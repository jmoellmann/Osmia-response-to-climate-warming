---
title: "Sex determination analysis"
author: "Jannik Möllmann"
date: "2022-11-21"
output: html_document
---

This script is mainly for documentation purposes. 
The data tables necessary to rerun this script are however
subsettable from the raw data (supplemental table 3)
supplied as supplemental information

```{r setup, include=FALSE}
knitr::opts_chunk$set(echo = TRUE)
```

## Data loading

```{r}
library(tidyverse)
library(factoextra)
library(cluster)
library(ggpubr)

#setwd("")

weights_wide <- read_tsv(file = "") %>% 
   dplyr::rename(population = pop) %>% arrange(species, population) %>% 
   mutate(relID = paste0(group, "-", ID)) %>% 
   dplyr::select(-ID, -group) %>% mutate(ID = 1:nrow(.))
sizes <- read_tsv(file = "") %>% 
   mutate(population = case_when(
      str_detect(population, "Nordpfalz") ~ "Pfalz",
      str_detect(population, "Schärding") ~ "Schärding",
      str_detect(population, "Südharz") ~ "Harz",
      TRUE ~ population
   )) %>%       
   arrange(species, population) %>%
   dplyr::select(-ID) %>% mutate(ID = 1:nrow(.))

df <- weights_wide %>% left_join(sizes, by = c("ID", "species", "population")) %>% 
   select(ID, relID, species:inferred, length:area)
```

```{r}
df %>% ggplot(aes(x = inferred, y = area, label = relID)) + geom_point() + 
   geom_text() + geom_smooth(method = "glm")
```

```{r}
cor(df$area, df$inferred)
```

```{r}
res.pca <- prcomp(df %>% select(-ID, -relID, -species, -population, 
                                -tube_full, -tube_empty) %>% as.matrix(), scale. = TRUE)
fviz_eig(res.pca)
```

```{r, warning=FALSE}
color_groups <- df %>% pull(relID) %>% str_extract("[BC]")

fviz_pca_biplot(res.pca,
             col.var = "#2E9FDF",
             col.ind = color_groups,
             gradient.cols = c("#00AFBB", "#E7B800", "#FC4E07"),
             repel = TRUE     # Avoid text overlapping
             )
```

## K-means clustering

```{r}
combinations <- df %>% group_by(species, population) %>% summarise() %>% ungroup()
scaled_dfs <- list()
inferred_sexes <- c()
optimal_k_plots <- list()
k_visualisation_plots <- list()
for (i in 1:nrow(combinations)){
   spcs <- as.character(combinations[i, "species"])
   pop <- as.character(combinations[i, "population"])
   scaled_df <- df %>% filter(species == spcs, population == pop) %>% as.data.frame()
      rownames(scaled_df) <- paste(scaled_df %>% pull(ID), sep = ":")
      scaled_df <- scaled_df %>% dplyr::select(inferred:area) %>% scale()
      scaled_dfs[[spcs]][[pop]] <- scaled_df
      km_temp <- kmeans(scaled_df, 2)[["cluster"]]
      mean_lens <- df %>% filter(species == spcs, population == pop) %>% 
         mutate(cluster = km_temp) %>% group_by(cluster) %>% 
         summarise(mean_len = mean(length)) %>% arrange(cluster) %>% pull(mean_len)
      if(mean_lens[1] > mean_lens[2]){
         km_temp <- replace(km_temp, km_temp == 1, "female")
         km_temp <- replace(km_temp, km_temp == 2, "male")
      } else{
         km_temp <- replace(km_temp, km_temp == 2, "female")
         km_temp <- replace(km_temp, km_temp == 1, "male")
      }
      inferred_sexes <- c(inferred_sexes, km_temp)
      gap_stat <- clusGap(scaled_df, FUN = kmeans, nstart = 25, K.max = 10, B = 50)
      optimal_k_plots[[paste(str_to_title(spcs), pop, sep = ":")]] <- gap_stat$Tab %>% 
         as_tibble() %>% ggplot(aes(x = 1:10, y = gap)) + geom_point() + geom_line() + 
         ylab("Score") + ggtitle(paste(str_to_title(spcs), pop, sep = ":")) + 
         scale_x_continuous(name = "K", breaks = seq(1, 10, 1)) 
}
```

```{r}
ggarrange(plotlist = optimal_k_plots, ncol = 4, nrow = 2)
```


```{r}
df_km <- df %>% mutate(inferred_sex = factor(inferred_sexes, 
                                               levels = c("male", "female")))
km_plot <- df_km %>% ggplot(aes(x = length, group = inferred_sex)) + 
   geom_density(aes(fill = inferred_sex, alpha = 0.5)) + 
   facet_wrap(vars(species, population), nrow = 2, ncol = 4) + 
   scale_fill_manual(values = c("#00BFC4", "#F8766D"))
km_plot
```

```{r}
#ggsave("", km_plot, width = 12, height = 7)
```

```{r}
ggplot(df_km, aes(x = inferred_sex, fill = inferred_sex)) + 
   geom_bar(show.legend = FALSE) + facet_wrap(vars(species, population), 
                                              nrow = 2, ncol = 4) + 
   scale_fill_manual(values = c("#00BFC4", "#F8766D"))
```

```{r}
#write_tsv(df_km, "")
#write_tsv(df, "")
```

### Testing

Now that for a lot of the data the true sex is known, we can start testing our 
model

```{r}
#full_df <- read_tsv("")
```

92% accuracy with k-means:
```{r}
full_df %>% select(sample_ID, species, sex, inferred_sex) %>% 
filter(!is.na(sex)) %>% mutate(correct = (sex == inferred_sex)) %>% 
group_by(species) %>% 
summarise(sum(correct) / nrow(.) * 2)

#90% accuracy for bicornis, 93% for cornuta
```
