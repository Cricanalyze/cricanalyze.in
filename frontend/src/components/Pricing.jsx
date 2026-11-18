import { useEffect, useState } from "react";
import { Tag } from "lucide-react";
import { api, inr } from "@/lib/api";

export const MAX_VIDEO_S = 25;
export const mrp = (price) => Math.round(Number(price || 0) * 1.5);

let offerReq = null;
export const useOfferTag = () => {
  const [tag, setTag] = useState("");
  useEffect(() => {
    offerReq = offerReq || api.get("/public/config").then(({ data }) => data.offer_tag || "").catch(() => "");
    offerReq.then(setTag);
  }, []);
  return tag;
};
export const resetOfferTag = () => { offerReq = null; };

export const OfferBadge = ({ tag, testid = "offer-tag" }) => tag ? (
  <span className="inline-flex items-center gap-1 rounded-full bg-[#F59E0B] text-[#0B132B] text-[11px] font-bold uppercase tracking-wide px-2.5 py-1" data-testid={testid}>
    <Tag size={12} />{tag}</span>) : null;

export const PriceBlock = ({ price, period, slug }) => (
  <div className="mt-4" data-testid={`price-${slug}`}>
    <div className="text-base text-slate-500 line-through" data-testid={`price-mrp-${slug}`}>{inr(mrp(price))}</div>
    <div className="text-4xl font-display font-extrabold">{inr(price)}<span className="text-sm text-slate-400 font-normal"> / {period} days</span></div>
    <p className="text-xs text-amber-300 mt-2" data-testid={`price-video-note-${slug}`}>Each video must be {MAX_VIDEO_S} seconds or shorter.</p>
  </div>
);

export const videoDuration = (file) => new Promise((resolve) => {
  const v = document.createElement("video");
  const url = URL.createObjectURL(file);
  v.preload = "metadata";
  v.onloadedmetadata = () => { URL.revokeObjectURL(url); resolve(v.duration); };
  v.onerror = () => { URL.revokeObjectURL(url); resolve(null); };
  v.src = url;
});
