import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Clock3, Search, Star, Upload } from "lucide-react";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

const MOCK_COLLECTION = [
  {
    name: "Finance",
    videos: [
      {
        id: "budgeting101",
        title: "Art of Budgeting",
        duration: "08:34",
        learners: 3,
        rating: 4.8,
        tags: ["cashflow", "essentials"],
        description: "Learn to manage your budget effectively.",
      },
      {
        id: "invest101",
        title: "Investing Basics",
        duration: "14:10",
        learners: 5,
        rating: 4.6,
        tags: ["portfolio", "stocks"],
        description: "Start investing with confidence.",
      },
    ],
  },
  {
    name: "Business",
    videos: [
      {
        id: "startup101",
        title: "Starting a Startup",
        duration: "12:47",
        learners: 4,
        rating: 4.3,
        tags: ["pitch", "growth"],
        description: "Steps to launch your startup.",
      },
    ],
  },
  { name: "Banking", videos: [] },
  { name: "Marketing", videos: [] },
  { name: "Estimation", videos: [] },
  // backend: replace static mock with GET /content/catalog grouped by category
];

export default function ContentDisplay() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    if (!query) return MOCK_COLLECTION;
    const lower = query.toLowerCase();
    return MOCK_COLLECTION.map((category) => {
      const matchCategory = category.name.toLowerCase().includes(lower);
      const videos = matchCategory
        ? category.videos
        : category.videos.filter((video) =>
            [video.title, video.description, ...(video.tags ?? [])]
              .join(" ")
              .toLowerCase()
              .includes(lower)
          );
      return { ...category, videos };
    }).filter((category) => category.videos.length > 0);
  }, [query]);

  return (
    <section className="space-y-8">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Content library
          </h1>
          <p className="text-sm text-muted-foreground">
            Curate and review every micro-lesson. Filter by topic, tags or
            contributor.
          </p>
        </div>
        <div className="flex gap-3">
          <div className="relative hidden sm:block">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search title, tag or author"
              className="w-72 pl-9"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              // backend: debounce and pass query to /content/search endpoint
            />
          </div>
          <Button onClick={() => navigate("/upload-content")}>
            Upload content
          </Button>
        </div>
      </header>

      <div className="sm:hidden">
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search content"
            className="pl-9"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
      </div>

      <Accordion
        type="single"
        collapsible
        className="rounded-xl border bg-card"
      >
        {filtered.map((category) => (
          <AccordionItem key={category.name} value={category.name}>
            <AccordionTrigger className="px-6 text-left">
              <div className="flex w-full items-center justify-between">
                <span className="text-base font-semibold">{category.name}</span>
                <Badge variant="secondary">
                  {category.videos.length} videos
                </Badge>
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-6">
              {category.videos.length ? (
                <ScrollArea className="w-full">
                  <div className="grid gap-4 py-4 sm:grid-cols-2 xl:grid-cols-3">
                    {category.videos.map((video) => (
                      <Card
                        key={video.id}
                        className="group flex cursor-pointer flex-col border-border/60 transition hover:border-primary"
                        onClick={() =>
                          navigate(`/content-management/${video.id}`)
                        }
                      >
                        <CardHeader className="gap-2">
                          <CardTitle className="text-base font-semibold">
                            {video.title}
                          </CardTitle>
                          <CardDescription>{video.description}</CardDescription>
                        </CardHeader>
                        <CardContent className="flex-1 space-y-3">
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Clock3 className="h-4 w-4" />
                            {video.duration}
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {video.tags?.map((tag) => (
                              <Badge
                                key={tag}
                                variant="outline"
                                className="capitalize"
                              >
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        </CardContent>
                        <CardFooter className="flex items-center justify-between border-t bg-muted/40 px-4 py-3 text-xs">
                          <span>{video.learners} active learners</span>
                          <span className="flex items-center gap-1 font-medium">
                            <Star className="h-3 w-3 text-amber-500" />
                            {video.rating}
                          </span>
                        </CardFooter>
                      </Card>
                    ))}
                  </div>
                </ScrollArea>
              ) : (
                <div className="py-6 text-sm text-muted-foreground">
                  No videos available yet.{" "}
                  {/* backend: surface CTA when category response is empty */}
                </div>
              )}
              <Separator className="my-4" />
              <div className="flex flex-wrap items-center justify-between gap-3 pb-4 text-xs text-muted-foreground">
                <span>
                  {/* backend: populate with contributor name and last updated timestamp */}
                  Last updated: awaiting sync
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  className="gap-2"
                  onClick={() => navigate("/upload-content")}
                >
                  <Upload className="h-3 w-3" />
                  Add video
                </Button>
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </section>
  );
}
