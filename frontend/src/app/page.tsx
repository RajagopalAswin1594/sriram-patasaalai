import Link from "next/link";

export default function PublicHomePage() {
  return (
    <main className="min-h-screen bg-stone-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <p className="text-lg font-semibold text-saffron-800">Digital Veda Gurukulam</p>
          <nav className="flex gap-4 text-sm">
            <Link href="/apply" className="text-stone-600 hover:text-saffron-700">Apply</Link>
            <Link href="/donate" className="text-stone-600 hover:text-saffron-700">Donate</Link>
            <Link href="/feedback" className="text-stone-600 hover:text-saffron-700">Gurukulam Feedback</Link>
            <Link href="/alumni/register" className="text-stone-600 hover:text-saffron-700">Alumni</Link>
            <Link href="/login" className="rounded-lg bg-saffron-600 px-3 py-1.5 font-medium text-white">Sign in</Link>
          </nav>
        </div>
      </header>

      <section className="mx-auto max-w-5xl px-6 py-20 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-stone-900 md:text-5xl">
          Preserving the Gurukulam tradition, digitally
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-stone-600">
          Admissions, Vedic curriculum, practice recordings, hostel management, donations, and community — one platform for the Patasala.
        </p>
        <div className="mt-10 flex flex-wrap justify-center gap-4">
          <Link href="/apply" className="rounded-lg bg-saffron-600 px-6 py-3 font-semibold text-white hover:bg-saffron-700">
            Apply for admission
          </Link>
          <Link href="/donate" className="rounded-lg border border-saffron-600 px-6 py-3 font-semibold text-saffron-700 hover:bg-saffron-50">
            Support Annadanam
          </Link>
        </div>
      </section>

      <section className="border-t bg-white py-16">
        <div className="mx-auto grid max-w-5xl gap-8 px-6 md:grid-cols-3">
          {[
            { title: "Admissions", desc: "Online applications, document review, and enrollment." },
            { title: "Learning", desc: "Syllabus, audio/video lessons, practice, and AI chant feedback." },
            { title: "Community", desc: "Events, Dharma forums, and alumni network." },
          ].map((item) => (
            <div key={item.title} className="rounded-xl border p-6">
              <h2 className="font-semibold text-stone-900">{item.title}</h2>
              <p className="mt-2 text-sm text-stone-600">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
