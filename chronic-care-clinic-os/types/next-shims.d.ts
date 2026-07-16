declare module "next/link" {
  import type { AnchorHTMLAttributes, ReactNode } from "react";

  export type LinkProps = AnchorHTMLAttributes<HTMLAnchorElement> & {
    href: string;
    children?: ReactNode;
    prefetch?: boolean;
    replace?: boolean;
    scroll?: boolean;
    shallow?: boolean;
    locale?: string | false;
  };

  export default function Link(props: LinkProps): JSX.Element;
}

declare module "next/navigation" {
  export function notFound(): never;
}
