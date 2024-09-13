"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Trash2,
  Edit,
  MoreVertical,
  Wand2,
  Sparkles,
  BarChart2,
  Download,
  Settings,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import Link from "next/link";

type Project = {
  id: number;
  name: string;
  description: string;
  lastUpdated: string;
  active: boolean;
};

export default function Component() {
  const [projects, setProjects] = useState<Project[]>([
    {
      id: 1,
      name: "Customer Data",
      description: "Clean and normalize customer information",
      lastUpdated: "2023-05-15",
      active: true,
    },
    {
      id: 2,
      name: "Sales Records",
      description: "Remove duplicates and standardize formats",
      lastUpdated: "2023-05-10",
      active: true,
    },
    {
      id: 3,
      name: "Product Catalog",
      description: "Update product descriptions and categories",
      lastUpdated: "2023-05-05",
      active: true,
    },
    {
      id: 4,
      name: "Employee Database",
      description: "Standardize job titles and departments",
      lastUpdated: "2023-05-20",
      active: true,
    },
  ]);

  const handleDeleteProject = (id: number) => {
    setProjects(projects.filter((project) => project.id !== id));
  };

  const handleEditProject = (id: number) => {
    console.log(`Editing project with id: ${id}`);
  };

  const handleAIFeature = (id: number) => {
    console.log(`Applying AI features to project with id: ${id}`);
  };

  const handleDataCleaning = (id: number) => {
    console.log(`Starting data cleaning for project with id: ${id}`);
  };

  const handleAnalyze = (id: number) => {
    console.log(`Analyzing data for project with id: ${id}`);
  };

  const handleExport = (id: number) => {
    console.log(`Exporting data for project with id: ${id}`);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <header className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-4xl font-bold text-gray-100">
            Active Projects Dashboard
          </h1>
          <Link href="/projects">
            <Button variant="outline">
              <Settings className="mr-2 h-4 w-4" />
              Manage Projects
            </Button>
          </Link>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects
          .filter((project) => project.active)
          .map((project) => (
            <Card
              key={project.id}
              className="w-full bg-gray-800 border-gray-700"
            >
              <CardHeader>
                <CardTitle className="flex justify-between items-center text-gray-100">
                  <span className="truncate">{project.name}</span>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-gray-300 hover:text-gray-100"
                      >
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent
                      align="end"
                      className="bg-gray-800 text-gray-100"
                    >
                      <DropdownMenuItem
                        onClick={() => handleEditProject(project.id)}
                        className="hover:bg-gray-700"
                      >
                        <Edit className="mr-2 h-4 w-4" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => handleDeleteProject(project.id)}
                        className="hover:bg-gray-700"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </CardTitle>
                <CardDescription className="text-gray-400">
                  {project.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-400 mb-4">
                  Last updated: {project.lastUpdated}
                </p>
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleAIFeature(project.id)}
                    className="text-gray-300 hover:text-gray-100 border-gray-600 hover:bg-gray-700"
                  >
                    <Wand2 className="mr-2 h-4 w-4" />
                    AI Features
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDataCleaning(project.id)}
                    className="text-gray-300 hover:text-gray-100 border-gray-600 hover:bg-gray-700"
                  >
                    <Sparkles className="mr-2 h-4 w-4" />
                    Clean Data
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleAnalyze(project.id)}
                    className="text-gray-300 hover:text-gray-100 border-gray-600 hover:bg-gray-700"
                  >
                    <BarChart2 className="mr-2 h-4 w-4" />
                    Analyze
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleExport(project.id)}
                    className="text-gray-300 hover:text-gray-100 border-gray-600 hover:bg-gray-700"
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Export
                  </Button>
                </div>
              </CardContent>
              {/* <CardFooter className="flex justify-end">
              <Button variant="outline" size="sm" onClick={() => handleEditProject(project.id)} className="text-gray-300 hover:text-gray-100 border-gray-600 hover:bg-gray-700">
                <Edit className="mr-2 h-4 w-4" />
                Edit Project
              </Button>
            </CardFooter> */}
            </Card>
          ))}
      </div>
    </div>
  );
}
