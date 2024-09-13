"use client";
import { usePathname } from "next/navigation";
import { GrCatalog } from "react-icons/gr";
import { CiCreditCard1, CiCalendarDate, CiUser } from "react-icons/ci";
import { LuPackage } from "react-icons/lu";
import { TiDocumentText } from "react-icons/ti";

export default function Aside() {
  const currentRoute = usePathname();
  const routes = [
    { route: "/home/catalog", icon: <GrCatalog />, name: "Projects" },
    { route: "/home/orders", icon: <LuPackage />, name: "Active Projects" },
    { route: "/home/customers", icon: <CiUser />, name: "Visualizer" },
    {
      route: "/home/subscription",
      icon: <CiCreditCard1 />,
      name: "Cleaner",
    },
    {
      route: "/home/appointments",
      icon: <CiCalendarDate />,
      name: "Chat with data",
    },
  ];

  return (
    <aside className="w-56 bg-gray-800 h-screen top-0 left-0 flex flex-col justify-start py-8 px-4 shadow-lg">
      <div className="space-y-6">
        {routes.map((route, index) => (
          <div
            className={`flex items-center gap-4 p-3 rounded-lg transition-colors ${
              currentRoute === route.route
                ? "bg-indigo-600 text-white"
                : "text-gray-400 hover:bg-gray-700 hover:text-white"
            }`}
            key={`route-${index}`}
          >
            <span className="text-xl">{route.icon}</span>
            <a href={route.route} className="text-lg font-medium">
              {route.name}
            </a>
          </div>
        ))}
      </div>
    </aside>
  );
}
