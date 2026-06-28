import { redirect } from "next/navigation";

export default function FeedbackIndexPage() {
  redirect("/dashboard/feedback/submit");
}
