"use strict";

function inferRepositoryUrl() {
  const repository = document.body.dataset.repository;
  const host = window.location.hostname;
  if (host.endsWith(".github.io")) {
    const owner = host.slice(0, -".github.io".length);
    return `https://github.com/${owner}/${repository}`;
  }
  return null;
}

function configureRepositoryLinks() {
  const repositoryUrl = inferRepositoryUrl();
  if (!repositoryUrl) return;
  document.querySelectorAll(".repo-link").forEach((link) => {
    const path = link.dataset.repoPath || "";
    link.href = path ? `${repositoryUrl}/${path}` : repositoryUrl;
  });
}

function configureNavigation() {
  const toggle = document.querySelector(".nav-toggle");
  const links = document.querySelector(".nav-links");
  if (!toggle || !links) return;
  toggle.addEventListener("click", () => {
    const isOpen = links.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });
  links.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      links.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    });
  });
}

function configureCopyButtons() {
  document.querySelectorAll("[data-copy-target]").forEach((button) => {
    button.addEventListener("click", async () => {
      const target = document.getElementById(button.dataset.copyTarget);
      if (!target) return;
      const original = button.textContent;
      try {
        await navigator.clipboard.writeText(target.innerText);
        button.textContent = "Copied";
      } catch {
        button.textContent = "Select text to copy";
      }
      window.setTimeout(() => {
        button.textContent = original;
      }, 1800);
    });
  });
}

function configureLightbox() {
  const dialog = document.getElementById("lightbox");
  if (!dialog || typeof dialog.showModal !== "function") return;
  const image = dialog.querySelector("img");
  const caption = dialog.querySelector("p");
  const close = dialog.querySelector(".lightbox-close");
  document.querySelectorAll(".zoomable").forEach((source) => {
    source.addEventListener("click", () => {
      image.src = source.src;
      image.alt = source.alt;
      const figureCaption = source.closest("figure")?.querySelector("figcaption");
      caption.textContent = figureCaption?.innerText || source.alt;
      dialog.showModal();
    });
  });
  close.addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
}

configureRepositoryLinks();
configureNavigation();
configureCopyButtons();
configureLightbox();
