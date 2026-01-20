export type Device = {
  mac: string;
  name: string;
  status: "online" | "offline";
};

export type Agent = {
  id: string;
  name: string;
  model: string;
};
