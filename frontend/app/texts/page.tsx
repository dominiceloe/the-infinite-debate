"use client";

import { useState, useEffect, useRef } from "react";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  CircularProgress,
  Alert,
  Paper,
} from "@mui/material";
import { Book, Person, CalendarMonth, MenuBook } from "@mui/icons-material";
import Link from "next/link";
import Image from "next/image";
import Header from "@/components/Header";
import { fetchTexts, fetchTextsStats } from "@/lib/api/texts";
import { PrimaryText } from "@/types/texts";

function TextCard({ text }: { text: PrimaryText }) {
  const [imageError, setImageError] = useState(false);
  const personaSlug = text.author
    .toLowerCase()
    .replace(/['\s.]/g, "-")
    .replace(/\./g, "");
  const portraitUrl = `/portraits/${personaSlug}.png`;

  return (
    <Card sx={{ display: "flex", flexDirection: "column", height: "100%", width: "100%", minWidth: 0 }}>
      <CardContent sx={{ flexGrow: 1, display: "flex", flexDirection: "column" }}>
        <Box sx={{ display: "flex", alignItems: "flex-start", gap: 2, mb: 2 }}>
          <Box
            sx={{
              width: 64,
              height: 64,
              borderRadius: 1,
              overflow: "hidden",
              flexShrink: 0,
              bgcolor: "grey.200",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Image
              src={imageError ? "/portraits/default.svg" : portraitUrl}
              alt={text.author}
              width={64}
              height={64}
              style={{ objectFit: "cover", width: "100%", height: "100%" }}
              onError={() => setImageError(true)}
            />
          </Box>
          <Box sx={{ flexGrow: 1, minWidth: 0 }}>
            <Typography
              variant="h6"
              component="h2"
              gutterBottom
              sx={{
                fontSize: "1.125rem",
                lineHeight: 1.3,
                overflow: "hidden",
                textOverflow: "ellipsis",
                display: "-webkit-box",
                WebkitLineClamp: 2,
                WebkitBoxOrient: "vertical",
              }}
            >
              {text.title}
            </Typography>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <Person fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary" noWrap>
                {text.author}
              </Typography>
            </Box>
          </Box>
        </Box>

        {text.translator && (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mb: 1 }}
            noWrap
          >
            Translated by {text.translator}
          </Typography>
        )}

        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 2 }}>
          <Chip
            label={text.category}
            size="small"
            color="primary"
            variant="outlined"
          />
          <Chip
            label={text.era.replace("_", " ")}
            size="small"
            color="secondary"
            variant="outlined"
          />
          {text.publication_year && (
            <Chip
              icon={<CalendarMonth fontSize="small" />}
              label={text.publication_year}
              size="small"
              variant="outlined"
            />
          )}
        </Box>

        <Typography variant="body2" color="text.secondary">
          <Book fontSize="small" sx={{ verticalAlign: "middle", mr: 0.5 }} />
          {text.section_count} sections
        </Typography>

        {text.description && (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              mt: 2,
              overflow: "hidden",
              textOverflow: "ellipsis",
              display: "-webkit-box",
              WebkitLineClamp: 3,
              WebkitBoxOrient: "vertical",
            }}
          >
            {text.description}
          </Typography>
        )}
      </CardContent>

      <CardActions sx={{ px: 2, pb: 2, pt: 0 }}>
        <Box sx={{ width: "100%" }}>
          <Button
            component={Link}
            href={`/texts/${text.slug}`}
            fullWidth
            variant="contained"
            sx={{ mb: text.citation_count && text.citation_count > 0 ? 1 : 0 }}
          >
            Read Text
          </Button>
          {text.citation_count && text.citation_count > 0 && (
            <Typography
              variant="caption"
              color="text.secondary"
              textAlign="center"
              display="block"
            >
              Cited {text.citation_count} times in debates
            </Typography>
          )}
        </Box>
      </CardActions>
    </Card>
  );
}

const CATEGORIES = [
  { value: "", label: "All Categories" },
  { value: "philosophy", label: "Philosophy" },
  { value: "theology", label: "Theology" },
  { value: "science", label: "Science" },
  { value: "political", label: "Political Theory" },
  { value: "ethics", label: "Ethics" },
];

const ERAS = [
  { value: "", label: "All Eras" },
  { value: "ancient", label: "Ancient (Before 500 CE)" },
  { value: "medieval", label: "Medieval (500-1500)" },
  { value: "early_modern", label: "Early Modern (1500-1800)" },
  { value: "modern", label: "Modern (1800-1950)" },
  { value: "contemporary", label: "Contemporary (1950-Present)" },
];

export default function TextsLibraryPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [era, setEra] = useState("");
  const [ordering, setOrdering] = useState("-created_at");
  const loadMoreRef = useRef<HTMLDivElement>(null);

  const {
    data,
    isLoading,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ["texts", { search, category, era, ordering }],
    queryFn: ({ pageParam = 1 }) =>
      fetchTexts({ search, category, era, ordering, page: pageParam }),
    getNextPageParam: (lastPage) => {
      if (lastPage.next) {
        const url = new URL(lastPage.next);
        const page = url.searchParams.get('page');
        return page ? parseInt(page) : null;
      }
      return null;
    },
    initialPageParam: 1,
  });

  const { data: stats } = useQuery({
    queryKey: ["texts-stats"],
    queryFn: fetchTextsStats,
  });

  // Flatten all pages into single array
  const texts = data?.pages.flatMap(page => page.results) || [];
  const totalCount = data?.pages[0]?.count || 0;

  // Infinite scroll observer
  useEffect(() => {
    if (!loadMoreRef.current || !hasNextPage || isFetchingNextPage) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          fetchNextPage();
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(loadMoreRef.current);

    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  return (
    <>
      <Header backTo="/" backLabel="Back to Home" />
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h3" component="h1" gutterBottom>
            Primary Texts Library
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Explore philosophical, theological, and scientific works referenced
            in debates
          </Typography>

          {stats && (
            <Box sx={{ mt: 2 }}>
              <Chip
                icon={<MenuBook />}
                label={`${stats.total_texts} text${
                  stats.total_texts !== 1 ? "s" : ""
                }`}
              />
            </Box>
          )}
        </Box>

        {/* Filters */}
        <Box sx={{
          display: "grid",
          gridTemplateColumns: {
            xs: "1fr",
            sm: "repeat(4, 1fr)"
          },
          gap: 3,
          mb: 3
        }}>
          <TextField
            fullWidth
            label="Search titles, authors..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            variant="outlined"
          />
          <FormControl fullWidth>
            <InputLabel>Category</InputLabel>
            <Select
              fullWidth
              value={category}
              label="Category"
              onChange={(e) => setCategory(e.target.value)}
            >
              {CATEGORIES.map((cat) => (
                <MenuItem key={cat.value} value={cat.value}>
                  {cat.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth>
            <InputLabel>Era</InputLabel>
            <Select
              fullWidth
              value={era}
              label="Era"
              onChange={(e) => setEra(e.target.value)}
            >
              {ERAS.map((e) => (
                <MenuItem key={e.value} value={e.value}>
                  {e.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth>
            <InputLabel>Sort</InputLabel>
            <Select
              fullWidth
              value={ordering}
              label="Sort"
              onChange={(e) => setOrdering(e.target.value)}
            >
              <MenuItem value="-created_at">Newest</MenuItem>
              <MenuItem value="created_at">Oldest</MenuItem>
              <MenuItem value="title">Title (A-Z)</MenuItem>
              <MenuItem value="-title">Title (Z-A)</MenuItem>
              <MenuItem value="author">Author (A-Z)</MenuItem>
              <MenuItem value="-word_count">Longest</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {/* Loading State */}
        {isLoading && (
          <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
            <CircularProgress />
          </Box>
        )}

        {/* Error State */}
        {error && (
          <Alert severity="error" sx={{ mb: 4 }}>
            Failed to load texts. Please try again.
          </Alert>
        )}

        {/* Results */}
        {!isLoading && !error && (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Showing {texts.length} of {totalCount} text{totalCount !== 1 ? "s" : ""}
            </Typography>

            {texts.length === 0 ? (
              <Alert severity="info">
                No texts found matching your filters. Try adjusting your search
                criteria.
              </Alert>
            ) : (
              <>
                <Box sx={{
                  display: "grid",
                  gridTemplateColumns: {
                    xs: "repeat(2, 1fr)",
                    lg: "repeat(4, 1fr)"
                  },
                  gap: 3
                }}>
                  {texts.map((text: PrimaryText) => (
                    <TextCard key={text.id} text={text} />
                  ))}
                </Box>

                {/* Load More Trigger */}
                {hasNextPage && (
                  <Box
                    ref={loadMoreRef}
                    sx={{
                      display: "flex",
                      justifyContent: "center",
                      py: 4
                    }}
                  >
                    {isFetchingNextPage && <CircularProgress />}
                  </Box>
                )}
              </>
            )}
          </>
        )}
      </Container>
    </>
  );
}
