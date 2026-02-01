// File: CSAirlines.java  Author: Alan Kennedy  Date: Jan. 14, 2013
// Description: This class creates a number of different Flight objects and exercises the
//              methods of the various classes.

public class CSAirlines {
   public static void main(String[] args) {
      Cargo c1 = new Cargo("Vancouver", "Pearson", new Time(8,30), new Time(4,0), "Hockey Sticks");
      Cargo c2 = new Cargo("Calgary", "Hamilton", new Time(9,22), new Time(3,20), "Diamonds");
      Domestic d1 = new Domestic("Vancouver", "Victoria", new Time(10,11), new Time(0,35), 15.00, 10.00);
      Domestic d2 = new Domestic("Kelowna", "Victoria", new Time(12,55), new Time(1,05), 15.00, 10.00);
      International i1 = new International("Vancouver", "Las Vegas", new Time(17,0), new Time(2,45), 15.00, "United States");
      International i2 = new International("Vancouver", "Paris", new Time(20,50), new Time(11,30), 25.00, "France");

      i2.setStatus("Delayed");
      d1.setStatus("Cancelled");

      System.out.println("" + c1 + c2 + d1 + d2 + i1 + i2);
   }
}