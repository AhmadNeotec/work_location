export default [
  {
    path: "/checkin",
    name: "EmployeeCheckinView",
    component: () => import("./views/checkin.vue"), // your custom one
  },
];
